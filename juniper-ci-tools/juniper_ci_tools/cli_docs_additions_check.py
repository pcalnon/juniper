"""Command-line entry point for :program:`juniper-docs-additions-check`.

Wraps :func:`juniper_ci_tools.docs_additions_check.run` with argparse and a
text/JSON reporter so the markdown deletion-magnitude screen (sequence-safety
gate G2 / G3) can run directly from CI or a local preflight. The screen FAILs on
a deleted Markdown heading or a run of ``>= N`` consecutive deleted lines between
BASE and HEAD.

Usage::

    juniper-docs-additions-check --base <ref> --head <ref>            # universal docs scope
    juniper-docs-additions-check --base <ref> --head <ref> --min-run 8
    juniper-docs-additions-check --base <ref> --head <ref> --scope 'guides/**/*.md'
    juniper-docs-additions-check --base <ref> --head <ref> --advisory --json

    python -m juniper_ci_tools.cli_docs_additions_check --help          # module form

Scope. With no ``--scope`` the universal docs cluster is used (``AGENTS.md`` +
``docs/**/*.md`` + ``notes/**/*.md``); this default is identical across every
Juniper repo. Pass one or more ``--scope GLOB`` (repeatable, POSIX ``**``
recursion) to screen a different markdown surface; a path is then in scope iff it
matches any glob AND ends ``.md``. An explicit ``--files`` list bypasses the
scope filter (any ``.md`` path).

Escape hatch: an ``Allow-Docs-Rewrite: <path>[, ...]`` commit trailer in the
BASE..HEAD range waives the enumerated files (``*`` waives all). ``--advisory``
prints findings but exits 0 even on an unwaived FAIL (the per-PR ``docs-rewrite``
label hatch, demoted to WARN-only); exit 2 (invocation error) is never masked.

Exit codes: 0 = clean (no unwaived FAIL), 1 = >= 1 unwaived FAIL, 2 = usage /
invocation error.
"""

from __future__ import annotations

import argparse
import json
import sys

from juniper_ci_tools._version import __version__
from juniper_ci_tools.docs_additions_check import DEFAULT_MIN_RUN, run


def _print_human(report: dict) -> None:
    st = report["stats"]
    print("=== sequence-safety: docs deletion-magnitude screen ===")
    print(f"base={report['base'][:12]} head={report['head'][:12]} min_run={report['min_run']}")
    print(f"files_screened={st['files_screened']} findings={st['findings_total']} fail={st['fail_count']} by_reason={st['by_reason']}")
    if st["waived_files"] or st["wildcard_waiver"]:
        waived = "*" if st["wildcard_waiver"] else ", ".join(st["waived_files"])
        print(f"waived (Allow-Docs-Rewrite): {waived}")
    print()
    for f in report["findings"]:
        print(f"    [{f['severity']}/{f['reason']}] {f['path']}  {f['detail']}")
    if st["fail_count"]:
        print(f"\nFAIL: {st['fail_count']} unwaived docs-deletion finding(s). Declare intentional rewrites with a `Allow-Docs-Rewrite: <path>` commit trailer.")
    else:
        print("\nOK: no unwaived docs-deletion findings.")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="juniper-docs-additions-check",
        description="Docs deletion-magnitude screen: FAIL on a deleted heading or a run of >= N consecutive deleted lines between BASE and HEAD.",
        epilog=("Default scope (no --scope): AGENTS.md (+ CLAUDE.md symlink), docs/**/*.md, notes/**/*.md. Pass one or more --scope GLOB (repeatable, POSIX ** recursion) to screen a different surface; a path is in scope iff it matches any glob AND ends .md. An explicit --files list bypasses scope. Exit 0=clean, 1=findings, 2=usage. Escape hatch: a `Allow-Docs-Rewrite: <path>[, ...]` commit trailer in the BASE..HEAD range waives the enumerated files (`*` waives all)."),
    )
    parser.add_argument("--base", required=True, help="base ref (e.g. origin/main, <merge>^1, github.event.before)")
    parser.add_argument("--head", required=True, help="head ref (e.g. HEAD, <merge>, github.sha)")
    parser.add_argument("--files", nargs="*", default=None, help="explicit .md files to screen (bypasses the scope filter)")
    parser.add_argument("--repo-root", default=".", help="repository root the git commands run in (default: cwd)")
    parser.add_argument(
        "--scope",
        action="append",
        default=None,
        metavar="GLOB",
        help="POSIX path glob selecting the screened markdown surface (repeatable). With no --scope, the universal docs cluster (AGENTS.md + docs/**/*.md + notes/**/*.md) is used verbatim.",
    )
    parser.add_argument("--min-run", type=int, default=DEFAULT_MIN_RUN, help=f"consecutive-deletion FAIL threshold (default: {DEFAULT_MIN_RUN})")
    parser.add_argument(
        "--advisory",
        action="store_true",
        help="advisory mode: print findings but exit 0 even on an unwaived FAIL (the per-PR docs-rewrite label hatch, demoted to WARN-only; the Allow-Docs-Rewrite commit trailer stays the primary waiver). Exit 2 (invocation error) is never masked.",
    )
    parser.add_argument("--json", action="store_true", help="emit the machine-readable report to stdout")
    parser.add_argument("--version", action="version", version="juniper-docs-additions-check {}".format(__version__))
    return parser


def main(argv: "list[str] | None" = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.min_run < 1:
        print("ERROR: --min-run must be >= 1", file=sys.stderr)
        return 2

    code, report = run(args.repo_root, args.base, args.head, args.files, args.min_run, args.scope)
    if code == 2:
        print(f"ERROR: {report.get('error', 'invocation error')}", file=sys.stderr)
        return 2
    report["advisory"] = args.advisory
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True))
    else:
        _print_human(report)
        if args.advisory and code == 1:
            print("\nADVISORY (--advisory): the FAIL finding(s) above are downgraded to WARN-only for this run; exit 0. The auditable `Allow-Docs-Rewrite: <path>` commit trailer remains the primary waiver.")
    return 0 if (args.advisory and code == 1) else code


if __name__ == "__main__":
    sys.exit(main())
