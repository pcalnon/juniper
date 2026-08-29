#!/usr/bin/env python3
"""Fork-safety import-surface scanner for a forkserver preload candidate (cascor#569, F3).

Project:     juniper-ml
Sub-Project: ad-hoc tooling
Author:      Paul Calnon
Created:     2026-08-26
Status:      ad-hoc -- one-off (cascor#569 fork-safety audit of the trainer's import closure)
Retire when: RETAINED (owner policy 2026-08-25 -- no retirement deadline). Previously: cascor#569 is
             merged with the audit recorded on the issue; delete then.
Related:     cascor#569 (F3 preload set), cascor#570 (forkserver route), handoff
             prompts/thread-handoff_automated-prompts/HANDOFF_2026-08-25_perf-lane-closeout-563-attributed-586-570-568.md
             section 3.2 (the audit this script mechanises).

WHAT IT ANSWERS
Preloading a module in a forkserver runs that module's import-time side effects ONCE, in the
forkserver process, and every candidate worker then inherits the result across fork(). Anything
the import CREATES -- an open file handle, a lock, a thread, a socket, a CUDA context, a seeded
RNG, a registered atexit hook, an environment mutation -- becomes state shared by every worker.
That is the fork-safety hazard cascor#569 is blocked on.

This walks the FIRST-PARTY import closure of one or more entry modules under SRC_ROOT (parent
packages included, because ``import a.b.c`` executes ``a/__init__.py`` and ``a/b/__init__.py``
first) and reports every module-level statement that does more than define a name: bare calls,
call-valued assignments, ``with`` contexts, raises, and decorator calls -- including inside class
bodies and module-level ``if`` / ``try`` / ``with`` / ``for`` blocks, all of which execute at
import time. Each flagged statement is tagged with the hazard families it matches (HAZARDS).

It is a static SCREEN, not a proof. A flagged call may be harmless (a dataclass field default, a
dict literal built by ``dict(...)``); a hazard hidden inside a third-party import is out of scope
by design -- the third-party roots are listed so the reader can see what the closure pulls in, and
packages already on the preload list (torch, numpy) are shared today regardless of this audit.

Usage: 2026-08-26_fork_safety_import_surface.py <SRC_ROOT> <entry.module> [<entry.module> ...] [--show-safe]
Exit:  0 report written to stdout; 2 usage error.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

HAZARDS: dict[str, re.Pattern[str]] = {
    "atexit": re.compile(r"\batexit\.register\b"),
    "file-handle": re.compile(r"(?<![\w.])open\(|\bio\.(?:open|FileIO|TextIOWrapper)\(|\bPath\([^)]*\)\.open\(|\btempfile\."),
    "logging-config": re.compile(r"\blogging\.(?:basicConfig|config\.)|\bdictConfig\(|\bfileConfig\(|\bFileHandler\(|\bStreamHandler\("),
    "logger-instance": re.compile(r"\bgetLogger\(|\bLogger\(|\bLogConfig\("),
    "thread-or-lock": re.compile(r"\bthreading\.|\b(?:R?Lock|Semaphore|BoundedSemaphore|Event|Condition|Thread|Timer)\("),
    "queue": re.compile(r"\bQueue\(|\bqueue\.(?:Queue|SimpleQueue|LifoQueue|PriorityQueue)\("),
    "multiprocessing": re.compile(r"\bmultiprocessing\.|\bmp\.|\bBaseManager\b|\bSharedMemory\(|\bManager\(|\bset_start_method\(|\bget_context\("),
    "manager-register": re.compile(r"\.register\("),
    "process-or-fork": re.compile(r"\bsubprocess\.|\bPopen\(|\bos\.fork\b|\bos\.exec|\bos\.spawn|\bos\.system\("),
    "socket-or-network": re.compile(r"\bsocket\.|\bhttpx\.|\brequests\.|\burllib\.|\.connect\("),
    "cuda-or-threads": re.compile(r"\btorch\.cuda\b|\bset_num_threads\(|\bset_num_interop_threads\(|\bomp_|\bOMP_NUM_THREADS\b|\bMKL_NUM_THREADS\b"),
    "rng-seed": re.compile(r"\bmanual_seed\(|\brandom\.seed\(|\bnp\.random\.seed\(|\bdefault_rng\(|\bRandomState\("),
    "environ-mutation": re.compile(r"\bos\.environ\[[^\]]+\]\s*=|\bos\.environ\.(?:setdefault|update|pop)\(|\bos\.putenv\(|\bos\.unsetenv\("),
    "signal": re.compile(r"\bsignal\.signal\(|\bsignal\.set_wakeup_fd\("),
    "mmap": re.compile(r"\bmmap\."),
    "sys-mutation": re.compile(r"\bsys\.path\.(?:insert|append)\(|\bsys\.(?:settrace|setprofile|excepthook)\b|\bbuiltins\."),
}

SAFE_CALLEES = {
    # Pure constructors that build immutable-ish data at import; flagged only with --show-safe.
    "dict", "list", "set", "tuple", "frozenset", "range", "len", "int", "float", "str", "bool",
    "field", "dataclass", "namedtuple", "NamedTuple", "TypeVar", "Enum", "auto", "property",
    "staticmethod", "classmethod", "abstractmethod", "lru_cache", "cache", "wraps", "total_ordering",
    "Path", "pl.Path", "pathlib.Path", "os.path.join", "os.path.dirname", "os.path.abspath",
    "os.path.expanduser", "os.getenv", "os.environ.get", "datetime.timedelta", "timedelta", "getattr",
    "isinstance", "sorted", "reversed", "enumerate", "zip", "map", "filter", "min", "max", "sum", "abs",
    "round", "repr", "format", "type", "object", "super", "id", "hash", "chr", "ord", "join", "split",
    "strip", "lower", "upper", "replace", "format_map", "get", "items", "keys", "values", "copy",
    "deepcopy", "copy.deepcopy", "re.compile", "compile", "torch.tensor", "torch.device", "np.array",
    "np.float32", "np.float64", "torch.float32", "torch.float64", "nn.ReLU", "nn.Sigmoid", "nn.Tanh",
    "torch.relu", "torch.sigmoid", "torch.tanh", "logging.getLevelName", "logging.addLevelName",
    "os.cpu_count", "multiprocessing.cpu_count", "mp.cpu_count", "os.getpid", "uuid.uuid4",
    "version", "importlib.metadata.version", "sys.exit",
}


def dotted(node: ast.AST) -> str:
    """Render the callee of a Call (or any attribute chain) as a dotted name, '' if not a name."""
    if isinstance(node, ast.Call):
        return dotted(node.func)
    if isinstance(node, ast.Attribute):
        base = dotted(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    if isinstance(node, ast.Name):
        return node.id
    return ""


def module_file(src_root: Path, name: str) -> Path | None:
    rel = Path(*name.split("."))
    for cand in (src_root / rel.with_suffix(".py"), src_root / rel / "__init__.py"):
        if cand.is_file():
            return cand
    return None


def parent_packages(name: str) -> list[str]:
    parts = name.split(".")
    return [".".join(parts[:i]) for i in range(1, len(parts))]


class ModuleScan:
    def __init__(self, src_root: Path, name: str, path: Path, show_safe: bool) -> None:
        self.src_root = src_root
        self.name = name
        self.path = path
        self.show_safe = show_safe
        self.source = path.read_text(encoding="utf-8", errors="replace")
        self.tree = ast.parse(self.source, filename=str(path))
        self.first_party: set[str] = set()
        self.third_party: set[str] = set()
        self.flags: list[tuple[int, str, str, list[str], str]] = []  # (line, context, kind, tags, text)
        self.safe: list[tuple[int, str, str]] = []
        self.dynamic_imports: list[tuple[int, str]] = []

    # -- import resolution ---------------------------------------------------------------------
    def _resolve_from(self, node: ast.ImportFrom) -> None:
        if node.level and node.level > 0:
            base_parts = self.name.split(".")
            if self.path.name != "__init__.py":
                base_parts = base_parts[:-1]
            base_parts = base_parts[: len(base_parts) - (node.level - 1)] if node.level > 1 else base_parts
            base = ".".join(base_parts)
            mod = f"{base}.{node.module}" if node.module else base
        else:
            mod = node.module or ""
        self._add_module(mod)
        for alias in node.names:
            self._add_module(f"{mod}.{alias.name}", quiet=True)

    def _add_module(self, mod: str, quiet: bool = False) -> None:
        if not mod:
            return
        if module_file(self.src_root, mod) is not None:
            self.first_party.add(mod)
            for pkg in parent_packages(mod):
                if module_file(self.src_root, pkg) is not None:
                    self.first_party.add(pkg)
        elif not quiet:
            root = mod.split(".")[0]
            if module_file(self.src_root, root) is None:
                self.third_party.add(root)

    # -- statement classification ------------------------------------------------------------
    def _text(self, node: ast.AST) -> str:
        seg = ast.get_source_segment(self.source, node) or ""
        first = seg.strip().splitlines()[0] if seg.strip() else ""
        return first[:170]

    def _tags(self, text: str) -> list[str]:
        return [tag for tag, rx in HAZARDS.items() if rx.search(text)]

    def _calls_in(self, node: ast.AST) -> list[str]:
        return [dotted(n) for n in ast.walk(node) if isinstance(n, ast.Call)]

    def _flag(self, node: ast.AST, context: str, kind: str) -> None:
        text = self._text(node)
        callees = [c for c in self._calls_in(node) if c]
        tags = self._tags(ast.get_source_segment(self.source, node) or text)
        if not tags and callees and all(c in SAFE_CALLEES or c.split(".")[-1] in SAFE_CALLEES for c in callees):
            self.safe.append((node.lineno, context, text))
            return
        if not tags and not callees and kind == "expr":
            return
        self.flags.append((node.lineno, context, kind, tags, text))

    def _walk(self, body: list[ast.stmt], context: str) -> None:
        for node in body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self._add_module(alias.name)
            elif isinstance(node, ast.ImportFrom):
                self._resolve_from(node)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Call):
                        self._flag(dec, f"{context}@{node.name}", "decorator-call")
                # Function bodies do not execute at import; but a module-level import hidden inside a
                # function is worth knowing about for the preload question (lazy imports).
                for inner in ast.walk(node):
                    if isinstance(inner, (ast.Import, ast.ImportFrom)):
                        names = ", ".join(a.name for a in inner.names)
                        mod = getattr(inner, "module", None)
                        self.dynamic_imports.append((inner.lineno, f"{context}.{node.name}: {mod or ''} [{names}]"))
            elif isinstance(node, ast.ClassDef):
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Call):
                        self._flag(dec, f"{context}@class {node.name}", "decorator-call")
                self._walk(node.body, f"{context}::class {node.name}")
            elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                value = node.value
                if value is None:
                    continue
                if any(isinstance(n, ast.Call) for n in ast.walk(value)):
                    self._flag(node, context, "call-valued assignment")
                elif self.show_safe:
                    self.safe.append((node.lineno, context, self._text(node)))
            elif isinstance(node, ast.Expr):
                if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                    continue  # docstring
                self._flag(node, context, "bare call" if isinstance(node.value, ast.Call) else "expr")
            elif isinstance(node, ast.If):
                self._flag(node.test, f"{context}::if", "condition") if any(isinstance(n, ast.Call) for n in ast.walk(node.test)) else None
                self._walk(node.body, f"{context}::if")
                self._walk(node.orelse, f"{context}::else")
            elif isinstance(node, ast.Try):
                self._walk(node.body, f"{context}::try")
                for h in node.handlers:
                    self._walk(h.body, f"{context}::except")
                self._walk(node.orelse, f"{context}::try-else")
                self._walk(node.finalbody, f"{context}::finally")
            elif isinstance(node, ast.With):
                for item in node.items:
                    self._flag(item.context_expr, f"{context}::with", "with-context")
                self._walk(node.body, f"{context}::with")
            elif isinstance(node, (ast.For, ast.While)):
                self._flag(node, f"{context}::loop", "loop-at-import")
                self._walk(node.body, f"{context}::loop")
            elif isinstance(node, ast.Raise):
                self._flag(node, context, "raise-at-import")
            elif isinstance(node, (ast.Pass, ast.Global, ast.Nonlocal, ast.Delete, ast.Assert)):
                continue
            else:
                self._flag(node, context, type(node).__name__)

    def run(self) -> "ModuleScan":
        self._walk(self.tree.body, "<module>")
        return self


def main(argv: list[str]) -> int:
    show_safe = "--show-safe" in argv
    args = [a for a in argv if a != "--show-safe"]
    if len(args) < 2:
        print(__doc__.split("Usage:")[1].split("\n")[0].strip(), file=sys.stderr)
        return 2
    src_root = Path(args[0]).resolve()
    entries = args[1:]
    if not src_root.is_dir():
        print(f"not a directory: {src_root}", file=sys.stderr)
        return 2

    queue: list[str] = []
    for e in entries:
        queue.extend(parent_packages(e))
        queue.append(e)
    seen: dict[str, ModuleScan] = {}
    missing: list[str] = []
    while queue:
        name = queue.pop(0)
        if name in seen:
            continue
        path = module_file(src_root, name)
        if path is None:
            missing.append(name)
            continue
        scan = ModuleScan(src_root, name, path, show_safe).run()
        seen[name] = scan
        for dep in sorted(scan.first_party):
            if dep not in seen:
                queue.append(dep)

    third: set[str] = set()
    print(f"# Fork-safety import surface -- entries {entries} under {src_root}")
    print(f"# first-party closure: {len(seen)} modules (parent packages included); missing: {missing or 'none'}")
    print()
    total_flags = 0
    tag_counts: dict[str, int] = {}
    for name in sorted(seen):
        scan = seen[name]
        third |= scan.third_party
        rel = scan.path.relative_to(src_root)
        print(f"## {name}  ({rel})  first-party deps: {sorted(scan.first_party) or '-'}  third-party roots: {sorted(scan.third_party) or '-'}")
        if not scan.flags:
            print("   (no import-time calls or side-effect statements beyond imports/definitions)")
        for line, context, kind, tags, text in sorted(scan.flags):
            total_flags += 1
            for t in tags:
                tag_counts[t] = tag_counts.get(t, 0) + 1
            tag_s = ",".join(tags) if tags else "-"
            print(f"   {rel}:{line}  [{kind}]  hazards={tag_s}  {context}\n        {text}")
        if show_safe and scan.safe:
            for line, context, text in sorted(scan.safe):
                print(f"   {rel}:{line}  [safe]  {context}\n        {text}")
        if scan.dynamic_imports:
            print(f"   lazy/function-local imports ({len(scan.dynamic_imports)}):")
            for line, desc in sorted(scan.dynamic_imports):
                print(f"      :{line}  {desc}")
        print()
    print("# SUMMARY")
    print(f"#   modules in closure : {len(seen)}")
    print(f"#   flagged statements : {total_flags}")
    print(f"#   hazard tags        : {dict(sorted(tag_counts.items())) or '{}'}")
    print(f"#   third-party roots  : {sorted(third)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
