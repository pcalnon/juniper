"""Symbol-loss screen -- AST inventory of BASE vs HEAD (sequence-safety gate G1 / G3).

Library implementation behind the ``juniper-symbol-loss-check`` console script
(the thin argparse wrapper is :mod:`juniper_ci_tools.cli_symbol_loss_check`).
Productionized from the 2026-07-28 Cursor-fleet flood census (Proposal P2 S1;
juniper-ml ``notes/JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md``)
and migrated into ``juniper-ci-tools`` as the single, PyPI-distributed source of
truth (sequence-safety rollout plan
``notes/JUNIPER_2026-08-07_JUNIPER-ECOSYSTEM_SEQUENCE-SAFETY-ROLLOUT-PLAN.md`` Wave 0).

Builds an AST symbol inventory for every in-scope touched file at BASE and at HEAD
and classifies each symbol:

  * LOST       -- present at base, absent at head (the silent-deletion class: a def a
                  bad merge dropped, leaving no error behind -- nothing else in CI sees
                  a clean deletion). FAIL for def/class/method and bash functions;
                  WARN for a removed import / module constant (refactors churn those).
  * WEAKENED   -- body shrunk past threshold: ``cur_lines <= ratio * base_lines`` AND
                  ``base_lines - cur_lines >= min_delta`` (defaults 0.6 / 4, lifted from
                  the census WEAKEN_RATIO / WEAKEN_MIN_DELTA). FAIL (py) / WARN (bash).
  * DUPLICATED -- the same def/class/method id appears >= 2x at head (a fusion /
                  redefinition). FAIL (py) / WARN (bash). NOTE (P2 S0): fusion is
                  primarily netted by the REQUIRED pre-commit mypy (``no-redef``); this
                  verdict is a best-effort overlap, not the primary net. A ``@property``
                  getter and its ``@x.setter`` / ``@x.deleter`` share a method name and are
                  disambiguated with a ``.setter`` / ``.deleter`` key suffix so a legitimate
                  accessor pair is never a false DUPLICATED -- see ``_accessor_suffix``.

Verdicts are qualified (``method:Class.name``, ``func:name``, ``class:Name``,
``const:NAME``, ``import:name``) so a bare-name collision cannot mask a real deletion.

Relocation (moves / renames are not loss). A ``LOST`` symbol is downgraded to
``RELOCATED`` (WARN, never FAIL) ONLY when the *qualified* key reappears in another
changed file at head, OR the deleted body matches a body newly present at head
(body-similarity). It is NEVER downgraded on a bare-name match -- test files reuse
``setUp`` / ``test_default`` across classes, so a bare lookup would mask a real
``TestA.test_default`` deletion behind an unrelated ``TestB.test_default`` (a
false-negative in the exact damage locus; P2 SF3).

Escape hatch. A ``Allow-Symbol-Loss: <qualified.symbol>[, ...]`` trailer in any commit
of the BASE..HEAD range waives the enumerated symbols (they become WAIVED, not FAIL).
It travels in git history so it works for BOTH the per-PR gate and the post-merge gate
(a PR label is invisible to ``push:main``). A blanket wildcard (``*``) is rejected so a
mass deletion cannot hide behind one marker.

Non-goal / blind spot. WEAKENED is a line-count heuristic: a *same-length* gutting
(replacing a body with ``assert True`` or swapping equal-line-count logic) has delta 0
and is invisible to it. That class needs mypy / human review, not this screen.

Scope. By default (no ``scope``) the historical juniper-ml predicate is used verbatim:
top-level ``tests/*.py`` + ``util/**/*.py`` + ``util/**/*.bash`` -- the census
``in_scope``. A caller may instead pass ``scope`` globs (from the CLI ``--scope`` flag)
to screen a different surface (e.g. ``src/**/*.py`` for an application-source repo); a
path is then in scope iff it matches any glob AND carries a screenable ``.py`` / ``.bash``
extension. An explicit ``files`` list bypasses the scope filter entirely (any
``.py`` / ``.bash`` path).

Exit codes (surfaced by the CLI): 0 = clean (no unwaived FAIL), 1 = >= 1 unwaived FAIL
finding, 2 = usage / invocation error. WARN / RELOCATED / WAIVED never fail.
"""

from __future__ import annotations

import ast
import re
import subprocess
from dataclasses import dataclass, field
from typing import Optional

# ---- config (lifted from the census screen) --------------------------------

WEAKEN_RATIO = 0.6  # flag when current_lines <= ratio * base_lines
WEAKEN_MIN_DELTA = 4  # ...and the absolute line delta is at least this
BODY_SIMILARITY_MIN_LINES = 3  # only body-match relocations for non-trivial bodies

# Verdict -> whether it is a hard finding (FAIL) for python vs bash. Relocation and
# waiver are applied afterwards and can only DOWNGRADE severity, never raise it.
_PY_FAIL_VERDICTS = frozenset({"LOST", "WEAKENED", "DUPLICATED"})
# For a removed import / module constant we only WARN (import/const churn is normal).
_ADVISORY_KINDS = frozenset({"import", "const"})


def in_scope(path: str) -> bool:
    """tests/*.py (top-level only), util/**/*.py, util/**/*.bash (census in_scope)."""
    if path.endswith(".py") and path.startswith("tests/") and "/" not in path[len("tests/") :]:
        return True
    if path.startswith("util/") and (path.endswith(".py") or path.endswith(".bash")):
        return True
    return False


# ---- scope globs (--scope override; POSIX path globs, 3.11-floor safe) ------


def _glob_to_regex(glob: str) -> str:
    """Translate a POSIX path glob into a regex source (used with ``re.fullmatch``).

    Explicit ``**`` recursion, so it does not depend on ``PurePath.full_match`` (3.13+,
    unavailable on the ci-tools 3.11 floor):

      * ``**/`` matches zero or more whole path segments, so ``src/**/*.py`` matches BOTH
        ``src/a.py`` and ``src/pkg/a.py``. A trailing / embedded ``**`` matches anything.
      * ``*`` matches within a single segment (any run of non-``/`` characters).
      * ``?`` matches a single non-``/`` character. Every other char is literal.
    """
    i, n = 0, len(glob)
    out: list[str] = []
    while i < n:
        c = glob[i]
        if c == "*":
            if i + 1 < n and glob[i + 1] == "*":
                i += 2
                if i < n and glob[i] == "/":
                    out.append("(?:[^/]+/)*")  # **/ -> zero or more whole segments
                    i += 1
                else:
                    out.append(".*")  # trailing / embedded ** -> anything
            else:
                out.append("[^/]*")  # * -> within a single segment
                i += 1
        elif c == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(c))
            i += 1
    return "".join(out)


def _match_scope(path: str, globs: list[str]) -> bool:
    """True iff ``path`` matches any glob in ``globs`` (POSIX path-glob semantics)."""
    return any(re.fullmatch(_glob_to_regex(g), path) is not None for g in globs)


# ---- git helpers -----------------------------------------------------------


def _git(root: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", root, *args], capture_output=True, text=True)


def resolve_ref(root: str, ref: str) -> Optional[str]:
    """Resolve a ref to a commit sha, or None if it does not resolve."""
    cp = _git(root, "rev-parse", "--verify", "-q", f"{ref}^{{commit}}")
    out = cp.stdout.strip()
    return out if cp.returncode == 0 and out else None


def blob_sha(root: str, ref: str, path: str) -> Optional[str]:
    """Resolve <ref>:<path> to a blob sha, or None if the path is absent there."""
    cp = _git(root, "rev-parse", "--verify", "-q", f"{ref}:{path}")
    out = cp.stdout.strip()
    return out if cp.returncode == 0 and out else None


def blob_text(root: str, sha: str) -> str:
    return _git(root, "cat-file", "-p", sha).stdout


def changed_files(root: str, base: str, head: str) -> list[str]:
    """Files changed on head since the merge-base of (base, head) -- the three-dot
    recipe the archive-guard uses. For the intended invocations (a PR merge ref;
    G3 ``<merge>^1``..``<merge>``) base is an ancestor of head, so the three-dot range
    degenerates to the plain ``base..head`` change set.
    """
    cp = _git(root, "diff", "--name-only", f"{base}...{head}")
    return [ln for ln in cp.stdout.splitlines() if ln]


def range_messages(root: str, base: str, head: str) -> str:
    """Concatenated commit messages for the base..head range (for trailer parsing)."""
    return _git(root, "log", "--format=%B", f"{base}..{head}").stdout


# ---- symbol extraction (lifted verbatim from the census screen) ------------


@dataclass
class Sym:
    lines: int
    chars: int
    count: int = 1  # occurrences of this id within a single blob (dup detect)
    body: str = ""  # normalized source segment (def/class/method only) for relocation


def _norm_body(seg: Optional[str]) -> str:
    if not seg:
        return ""
    return re.sub(r"\s+", " ", seg).strip()


def _seg_len(src: str, node: ast.AST) -> tuple[int, int, str]:
    try:
        seg = ast.get_source_segment(src, node)
    except Exception:
        seg = None
    if seg is not None:
        return seg.count("\n") + 1, len(seg), seg
    lo = getattr(node, "lineno", None)
    hi = getattr(node, "end_lineno", None)
    if lo and hi:
        return hi - lo + 1, 0, ""
    return 0, 0, ""


def _add(d: dict[str, Sym], key: str, lines: int, chars: int, body: str = "") -> None:
    if key in d:
        d[key].count += 1
        # keep the larger segment for a duplicated id
        if lines > d[key].lines:
            d[key].lines, d[key].chars, d[key].body = lines, chars, _norm_body(body)
    else:
        d[key] = Sym(lines, chars, body=_norm_body(body))


def _accessor_suffix(node: ast.AST) -> str:
    """Distinct key suffix for a ``@<name>.setter`` / ``@<name>.deleter`` accessor.

    A ``@property`` getter and its ``@x.setter`` / ``@x.deleter`` share a method name, so
    without disambiguation the two ``FunctionDef`` nodes collide on one qualified key and
    are miscounted as ``DUPLICATED`` -- a false positive on every PR touching such a file.
    Suffixing the setter / deleter keeps the getter's bare key (so ``LOST`` detection on the
    property is unchanged) while the accessors count independently.

    Backported from the juniper-cascor port (whose ``src/`` surface has such pairs, e.g.
    ``TrainingLifecycleManager.network``) for ecosystem consistency and forward safety
    when a repo scopes the screen (``--scope``) over application source.
    """
    for dec in getattr(node, "decorator_list", []):
        if isinstance(dec, ast.Attribute) and dec.attr in ("setter", "deleter"):
            return f".{dec.attr}"
    return ""


def _walk_class(src: str, cls: ast.ClassDef, prefix: str, out: dict[str, Sym]) -> None:
    for n in cls.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            ln, ch, seg = _seg_len(src, n)
            _add(out, f"method:{prefix}.{n.name}{_accessor_suffix(n)}", ln, ch, seg)
        elif isinstance(n, ast.ClassDef):
            ln, ch, seg = _seg_len(src, n)
            _add(out, f"class:{prefix}.{n.name}", ln, ch, seg)
            _walk_class(src, n, f"{prefix}.{n.name}", out)


def _target_names(t: ast.AST) -> list[str]:
    if isinstance(t, ast.Name):
        return [t.id]
    if isinstance(t, (ast.Tuple, ast.List)):
        names: list[str] = []
        for e in t.elts:
            names.extend(_target_names(e))
        return names
    return []


def py_symbols(src: str) -> Optional[dict[str, Sym]]:
    """Return None if the blob does not parse (record UNPARSEABLE upstream)."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None
    out: dict[str, Sym] = {}
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            ln, ch, seg = _seg_len(src, n)
            _add(out, f"func:{n.name}", ln, ch, seg)
        elif isinstance(n, ast.ClassDef):
            ln, ch, seg = _seg_len(src, n)
            _add(out, f"class:{n.name}", ln, ch, seg)
            _walk_class(src, n, n.name, out)
        elif isinstance(n, ast.Import):
            for a in n.names:
                _add(out, f"import:{a.asname or a.name}", 1, 0)
        elif isinstance(n, ast.ImportFrom):
            for a in n.names:
                _add(out, f"import:{a.asname or a.name}", 1, 0)
        elif isinstance(n, ast.Assign):
            for t in n.targets:
                for name in _target_names(t):
                    _add(out, f"const:{name}", 1, 0)
        elif isinstance(n, ast.AnnAssign):
            for name in _target_names(n.target):
                _add(out, f"const:{name}", 1, 0)
    return out


_BASH_FN = re.compile(r"^\s*(?:function\s+)?([A-Za-z_][A-Za-z0-9_-]*)\s*\(\s*\)\s*\{", re.M)
_BASH_FN2 = re.compile(r"^\s*function\s+([A-Za-z_][A-Za-z0-9_-]*)\s*(?:\(\s*\))?\s*\{?", re.M)


def bash_symbols(src: str) -> dict[str, Sym]:
    out: dict[str, Sym] = {}
    lines = src.splitlines()
    seen_line: dict[str, int] = {}
    for m in _BASH_FN.finditer(src):
        name = m.group(1)
        _add(out, f"fn:{name}", 1, 0)
        seen_line.setdefault(name, src[: m.start()].count("\n"))
    for m in _BASH_FN2.finditer(src):
        name = m.group(1)
        key = f"fn:{name}"
        if key not in out:
            _add(out, key, 1, 0)
            seen_line.setdefault(name, src[: m.start()].count("\n"))
    # crude body length: distance to next function or EOF (for the WEAKENED signal)
    starts = sorted(seen_line.items(), key=lambda kv: kv[1])
    for i, (name, ln) in enumerate(starts):
        end = starts[i + 1][1] if i + 1 < len(starts) else len(lines)
        out[f"fn:{name}"].lines = max(1, end - ln)
    return out


def symbols_for(path: str, src: str) -> tuple[Optional[dict[str, Sym]], bool]:
    """(symbols, parseable). symbols is None + parseable False for a py SyntaxError."""
    if path.endswith(".bash"):
        return bash_symbols(src), True
    syms = py_symbols(src)
    if syms is None:
        return None, False
    return syms, True


# ---- classification --------------------------------------------------------


def _kind(key: str) -> str:
    return key.split(":", 1)[0]


def _is_fail(verdict: str, key: str, is_bash: bool) -> bool:
    """Severity: bash verdicts other than LOST are WARN (the bash regex is crude);
    a removed import / module constant is WARN; everything else in the FAIL set FAILs."""
    if verdict not in _PY_FAIL_VERDICTS:
        return False
    if is_bash:
        return verdict == "LOST"  # bash: only unambiguous deletion is a hard FAIL
    if verdict == "LOST" and _kind(key) in _ADVISORY_KINDS:
        return False  # import / const removal -> advisory WARN only
    return True


@dataclass
class Finding:
    path: str
    symbol: str
    verdict: str  # LOST | WEAKENED | DUPLICATED | RELOCATED | WAIVED
    severity: str  # FAIL | WARN | WAIVED
    detail: dict = field(default_factory=dict)


def classify_file(path: str, base_inv: dict[str, Sym], head_inv: dict[str, Sym], is_bash: bool) -> list[Finding]:
    """Raw per-file verdicts (before cross-file relocation + trailer waivers)."""
    findings: list[Finding] = []
    for key, bsym in sorted(base_inv.items()):
        if key not in head_inv:
            verdict = "LOST"
            sev = "FAIL" if _is_fail(verdict, key, is_bash) else "WARN"
            findings.append(Finding(path, key, verdict, sev, {"base_lines": bsym.lines}))
            continue
        hsym = head_inv[key]
        kind = _kind(key)
        # DUPLICATED only for real definitions (import/const dups are noise).
        if kind in ("func", "class", "method", "fn") and hsym.count >= 2:
            verdict = "DUPLICATED"
            sev = "FAIL" if _is_fail(verdict, key, is_bash) else "WARN"
            findings.append(Finding(path, key, verdict, sev, {"head_count": hsym.count}))
            continue
        # WEAKENED only for bodies with a meaningful line count.
        if kind in ("func", "class", "method", "fn") and bsym.lines and hsym.lines:
            if hsym.lines <= WEAKEN_RATIO * bsym.lines and (bsym.lines - hsym.lines) >= WEAKEN_MIN_DELTA:
                verdict = "WEAKENED"
                sev = "FAIL" if _is_fail(verdict, key, is_bash) else "WARN"
                findings.append(
                    Finding(
                        path,
                        key,
                        verdict,
                        sev,
                        {"base_lines": bsym.lines, "head_lines": hsym.lines, "ratio": round(hsym.lines / bsym.lines, 2)},
                    )
                )
    return findings


def apply_relocation(findings: list[Finding], base_invs: dict[str, dict[str, Sym]], head_invs: dict[str, dict[str, Sym]]) -> None:
    """Downgrade a LOST finding to RELOCATED (WARN) when the QUALIFIED key reappears in
    another changed file at head, or the deleted body matches a body newly present at
    head. Never on a bare-name match (P2 SF3) -- keys are class-qualified throughout."""
    # qualified key -> set of files that hold it at head
    head_key_files: dict[str, set[str]] = {}
    for fpath, inv in head_invs.items():
        for key in inv:
            head_key_files.setdefault(key, set()).add(fpath)
    # bodies present at base anywhere (to require the head match be genuinely "new")
    base_bodies: set[str] = {s.body for inv in base_invs.values() for s in inv.values() if s.body}
    # non-trivial bodies newly present at head
    head_new_bodies: set[str] = {s.body for inv in head_invs.values() for s in inv.values() if s.body and s.body not in base_bodies and (s.body.count(" ") + 1) >= BODY_SIMILARITY_MIN_LINES}

    for f in findings:
        if f.verdict != "LOST":
            continue
        # qualified-name relocation: same class-qualified key in a DIFFERENT file at head
        elsewhere = head_key_files.get(f.symbol, set()) - {f.path}
        if elsewhere:
            f.verdict, f.severity = "RELOCATED", "WARN"
            f.detail = {**f.detail, "relocated_to": sorted(elsewhere), "match": "qualified-name"}
            continue
        # body-similarity relocation: the deleted body reappears verbatim at head
        bsym = base_invs.get(f.path, {}).get(f.symbol)
        if bsym and bsym.body and bsym.lines >= BODY_SIMILARITY_MIN_LINES and bsym.body in head_new_bodies:
            f.verdict, f.severity = "RELOCATED", "WARN"
            f.detail = {**f.detail, "match": "body-similarity"}


# ---- escape-hatch trailer parsing ------------------------------------------

_ALLOW_RE = re.compile(r"^\s*Allow-Symbol-Loss:\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE)


def parse_allow_trailers(messages: str) -> tuple[set[str], bool]:
    """Return (enumerated qualified names, wildcard_seen). A ``*`` (or bare/empty)
    value is a rejected blanket wildcard -- it waives nothing and is reported."""
    allowed: set[str] = set()
    wildcard = False
    for m in _ALLOW_RE.finditer(messages or ""):
        for tok in re.split(r"[,\s]+", m.group(1).strip()):
            tok = tok.strip()
            if not tok:
                continue
            if tok == "*":
                wildcard = True
                continue
            allowed.add(tok)
    return allowed, wildcard


def _waives(symbol_key: str, allowed: set[str]) -> bool:
    """A trailer token matches a finding by full key (``method:TestA.test_default``) or
    by the kind-stripped qualified name (``TestA.test_default``)."""
    if symbol_key in allowed:
        return True
    stripped = symbol_key.split(":", 1)[1] if ":" in symbol_key else symbol_key
    return stripped in allowed


def apply_waivers(findings: list[Finding], allowed: set[str]) -> None:
    for f in findings:
        if f.severity == "FAIL" and _waives(f.symbol, allowed):
            f.verdict, f.severity = "WAIVED", "WAIVED"
            f.detail = {**f.detail, "waived_by": "Allow-Symbol-Loss trailer"}


# ---- driver ----------------------------------------------------------------


def run(root: str, base: str, head: str, files: Optional[list[str]], scope: Optional[list[str]] = None) -> tuple[int, dict]:
    """Return (exit_code, report). exit_code: 0 clean, 1 findings, 2 invocation error.

    ``scope`` (from the CLI ``--scope`` flag) is an optional list of POSIX path globs.
    When None/empty the historical :func:`in_scope` predicate is used verbatim (so a
    default run is byte-identical to the pre-migration screen); otherwise a discovered
    path is in scope iff it matches any glob AND carries a ``.py`` / ``.bash`` extension.
    An explicit ``files`` list bypasses scope entirely.
    """
    base_sha = resolve_ref(root, base)
    head_sha = resolve_ref(root, head)
    if base_sha is None or head_sha is None:
        bad = base if base_sha is None else head
        return 2, {"error": f"could not resolve ref: {bad!r}"}

    if files:
        # Explicit list bypasses the scope filter; only .py / .bash are screenable.
        scoped = [p for p in files if p.endswith(".py") or p.endswith(".bash")]
        skipped = [p for p in files if p not in scoped]
    else:
        discovered = changed_files(root, base, head)
        if scope:
            # A discovered path is in scope iff it matches any --scope glob AND is screenable.
            scoped = [p for p in discovered if (p.endswith(".py") or p.endswith(".bash")) and _match_scope(p, scope)]
        else:
            # No --scope: reproduce the historical in_scope() predicate verbatim.
            scoped = [p for p in discovered if in_scope(p)]
        skipped = [p for p in discovered if p not in scoped]

    base_invs: dict[str, dict[str, Sym]] = {}
    head_invs: dict[str, dict[str, Sym]] = {}
    unparseable: list[str] = []
    findings: list[Finding] = []

    for path in sorted(set(scoped)):
        is_bash = path.endswith(".bash")
        bsha = blob_sha(root, base_sha, path)
        hsha = blob_sha(root, head_sha, path)
        b_inv: Optional[dict[str, Sym]] = None
        h_inv: Optional[dict[str, Sym]] = None
        if bsha is not None:
            b_inv, ok = symbols_for(path, blob_text(root, bsha))
            if not ok:
                unparseable.append(f"{base_sha[:9]}:{path}")
        if hsha is not None:
            h_inv, ok = symbols_for(path, blob_text(root, hsha))
            if not ok:
                unparseable.append(f"{head_sha[:9]}:{path}")
        # A file absent (or unparseable) at base contributes no base inventory -> no
        # LOST is inferred against nothing. An unparseable HEAD is surfaced as a note
        # (syntax is caught by check-ast / mypy, not this compositional screen).
        base_invs[path] = b_inv or {}
        head_invs[path] = h_inv or {}
        findings.extend(classify_file(path, base_invs[path], head_invs[path], is_bash))

    apply_relocation(findings, base_invs, head_invs)
    allowed, wildcard = parse_allow_trailers(range_messages(root, base_sha, head_sha))
    apply_waivers(findings, allowed)

    fails = [f for f in findings if f.severity == "FAIL"]
    by_verdict: dict[str, int] = {}
    for f in findings:
        by_verdict[f.verdict] = by_verdict.get(f.verdict, 0) + 1

    report = {
        "base": base_sha,
        "head": head_sha,
        "stats": {
            "files_screened": len(scoped),
            "skipped_out_of_scope": sorted(set(skipped)),
            "unparseable_blobs": sorted(set(unparseable)),
            "findings_total": len(findings),
            "fail_count": len(fails),
            "by_verdict": by_verdict,
            "waived_symbols": sorted(allowed),
            "wildcard_rejected": wildcard,
        },
        "findings": [{"path": f.path, "symbol": f.symbol, "verdict": f.verdict, "severity": f.severity, "detail": f.detail} for f in sorted(findings, key=lambda x: (x.path, x.symbol))],
    }
    return (1 if fails else 0), report
