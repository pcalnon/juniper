"""Command-line entry point for :program:`juniper-symbol-loss-check`.

Wraps :func:`juniper_ci_tools.symbol_loss_check.run` with argparse and a
text/JSON reporter so the AST symbol-loss screen (sequence-safety gate G1 / G3)
can run directly from CI or a local preflight. The screen FAILs when a
def/class/method (or bash function) is silently deleted, gutted past threshold,
or duplicated between BASE and HEAD.

Usage::

    juniper-symbol-loss-check --base <ref> --head <ref>            # default ml scope
    juniper-symbol-loss-check --base <ref> --head <ref> --scope 'src/**/*.py'
    juniper-symbol-loss-check --base <ref> --head <ref> --files a.py util/b.bash
    juniper-symbol-loss-check --base <ref> --head <ref> --advisory --json

    python -m juniper_ci_tools.cli_symbol_loss_check --help          # module form

Scope. With no ``--scope`` the built-in juniper-ml default is used verbatim
(top-level ``tests/*.py`` + ``util/**/*.py`` + ``util/**/*.bash``). Pass one or
more ``--scope GLOB`` (repeatable, POSIX path globs with ``**`` recursion) to
screen a different surface; a path is then in scope iff it matches any glob AND
carries a ``.py`` / ``.bash`` extension. An explicit ``--files`` list bypasses
the scope filter entirely.

Escape hatch: an ``Allow-Symbol-Loss: <qualified.symbol>[, ...]`` commit trailer
in the BASE..HEAD range waives the enumerated symbols (a ``*`` wildcard is
rejected). ``--advisory`` prints findings but exits 0 even on an unwaived FAIL
(the per-PR ``allow-symbol-loss`` label hatch, demoted to WARN-only); exit 2
(invocation error) is never masked.

Exit codes: 0 = clean (no unwaived FAIL), 1 = >= 1 unwaived FAIL, 2 = usage /
invocation error.
"""

from __future__ import annotations

import argparse
import json
import sys

from juniper_ci_tools._version import __version__
from juniper_ci_tools.symbol_loss_check import run


def _print_human(report: dict) -> None:
    st = report["stats"]
    print("=== sequence-safety: symbol-loss screen ===")
    print(f"base={report['base'][:12]} head={report['head'][:12]}")
    print(f"files_screened={st['files_screened']} findings={st['findings_total']} fail={st['fail_count']} by_verdict={st['by_verdict']}")
    if st["waived_symbols"]:
        print(f"waived (Allow-Symbol-Loss): {', '.join(st['waived_symbols'])}")
    if st["wildcard_rejected"]:
        print("NOTE: an Allow-Symbol-Loss: * wildcard was seen and REJECTED (waives nothing).")
    if st["unparseable_blobs"]:
        print(f"NOTE: unparseable blobs (out of scope for this screen): {', '.join(st['unparseable_blobs'])}")
    print()
    for f in report["findings"]:
        print(f"    [{f['severity']}/{f['verdict']}] {f['path']} :: {f['symbol']}  {f['detail']}")
    if st["fail_count"]:
        print(f"\nFAIL: {st['fail_count']} unwaived symbol-loss finding(s). Declare intentional removals with a `Allow-Symbol-Loss: <qualified.symbol>` commit trailer.")
    else:
        print("\nOK: no unwaived symbol-loss findings.")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="juniper-symbol-loss-check",
        description="AST symbol-loss screen: FAIL on a silently deleted / gutted / duplicated def between BASE and HEAD.",
        epilog=("Default scope (no --scope): top-level tests/*.py + util/**/*.py + util/**/*.bash. Pass one or more --scope GLOB (repeatable, POSIX ** recursion) to screen a different surface; a path is in scope iff it matches any glob AND is a .py/.bash file. An explicit --files list bypasses scope. Exit 0=clean, 1=findings, 2=usage. Escape hatch: a `Allow-Symbol-Loss: <qualified.symbol>[, ...]` commit trailer in the BASE..HEAD range waives the enumerated symbols (a `*` wildcard is rejected)."),
    )
    parser.add_argument("--base", required=True, help="base ref (e.g. origin/main, <merge>^1, github.event.before)")
    parser.add_argument("--head", required=True, help="head ref (e.g. HEAD, <merge>, github.sha)")
    parser.add_argument("--files", nargs="*", default=None, help="explicit .py/.bash files to screen (bypasses the scope filter)")
    parser.add_argument("--repo-root", default=".", help="repository root the git commands run in (default: cwd)")
    parser.add_argument(
        "--scope",
        action="append",
        default=None,
        metavar="GLOB",
        help="POSIX path glob selecting the screened surface (repeatable). With no --scope, the built-in juniper-ml default (tests/*.py + util/**) is used verbatim.",
    )
    parser.add_argument(
        "--advisory",
        action="store_true",
        help="advisory mode: print findings but exit 0 even on an unwaived FAIL (the per-PR allow-symbol-loss label hatch, demoted to WARN-only; the Allow-Symbol-Loss commit trailer stays the primary enumerated waiver). Exit 2 (invocation error) is never masked.",
    )
    parser.add_argument("--json", action="store_true", help="emit the machine-readable report to stdout")
    parser.add_argument("--version", action="version", version="juniper-symbol-loss-check {}".format(__version__))
    return parser


def main(argv: "list[str] | None" = None) -> int:
    args = _build_parser().parse_args(argv)

    code, report = run(args.repo_root, args.base, args.head, args.files, args.scope)
    if code == 2:
        print(f"ERROR: {report.get('error', 'invocation error')}", file=sys.stderr)
        return 2
    report["advisory"] = args.advisory
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True))
    else:
        _print_human(report)
        if args.advisory and code == 1:
            print("\nADVISORY (--advisory): the FAIL finding(s) above are downgraded to WARN-only for this run; exit 0. The auditable `Allow-Symbol-Loss: <qualified.symbol>` commit trailer remains the primary, enumerated waiver.")
    return 0 if (args.advisory and code == 1) else code


if __name__ == "__main__":
    sys.exit(main())
