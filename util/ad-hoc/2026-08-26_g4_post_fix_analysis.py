#!/usr/bin/env python3
"""Post-fix G4 analysis: decompose a paired campaign and count ungraceful worker stops per leg.

Project:     juniper-ml
Sub-Project: ad-hoc tooling
Author:      Paul Calnon
Created:     2026-08-26
Status:      ad-hoc -- one-off (cascor#586/#587 live re-measure; handoff 2026-08-25 section 3.1 step 1)
Retire when: RETAINED (owner policy 2026-08-25 -- no retirement deadline). Previously: the post-#587
             G4 table is posted to cascor#571 and the register's G4 row updated; delete then.
Related:     util/ad-hoc/2026-08-25_g4_overhead_decomposition.py (the instrument this drives);
             util/ad-hoc/2026-08-21_h2h_paired_campaign.bash (writes the legs.jsonl this reads).

WHY A SCRIPT
The campaign's SERVICE legs are not in its OUT_ROOT: legs.jsonl names each leg's suite_dir, and that
suite's registry.jsonl names the run_dir. Resolving them by suite-dir NAME would silently pair an
older campaign's service legs with this campaign's CLI legs (the 2026-08-25 legs sit right beside
these). So this resolves them from THIS campaign's own ledger and hands the instrument explicit
run dirs.

ACCEPTANCE IS A COUNT, NOT A TIME (handoff 2026-08-25 section 3.1). cascor#587 shipped two
independent changes: (a) the feeder-flush fix (cancel_join_thread + parent-side drain) and (b) a
SHARED 5 s grace + 1 s kill deadline replacing seven serial join(5.0)s. (b) alone caps teardown at
~10 s even if (a) is wrong, so train_other can never "stay high" on a #587 build and a time-only
reading would call a still-broken pool fixed. The discriminator is the number of
"did not stop gracefully" records per leg: 0 in every CLI leg confirms (a); any non-zero means (a)
is wrong or incomplete and (b) is masking it.

Usage: 2026-08-26_g4_post_fix_analysis.py <OUT_ROOT> [--pattern REGEX]
Exit:  0 report printed; 2 if the ledger cannot be resolved.
"""

from __future__ import annotations

import json
import re
# subprocess drives a sibling ad-hoc script with a fixed interpreter; every argument is a path read from a ledger.
import subprocess  # nosec B404
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DECOMPOSER = HERE / "2026-08-25_g4_overhead_decomposition.py"
UNGRACEFUL_DEFAULT = r"did not stop gra"


def read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def count_in_logs(log_dir: Path, pattern: re.Pattern[str]) -> tuple[int | None, list[str], list[str]]:
    """Count pattern matches across a run's trainer log AND its rotated siblings (juniper_cascor.log*).

    Returns ``(count, read, unreadable)``. ``count`` is **None** when nothing was
    actually read -- no log file present, or every candidate raised OSError.

    That distinction is load-bearing: this count IS the acceptance criterion for the
    #586 shutdown-tax fix ("0 ungraceful stops"), so a leg that produced no readable
    log must never render as a 0 and must never be summed into the total. Absence of
    evidence read as evidence of absence is the vacuous-pass class -- the machinery
    breaks and the report still says PASS.
    """
    files = sorted(log_dir.glob("juniper_cascor.log*"))
    total = 0
    read: list[str] = []
    unreadable: list[str] = []
    for f in files:
        try:
            with f.open("r", encoding="utf-8", errors="replace") as fh:
                for ln in fh:
                    if pattern.search(ln):
                        total += 1
        except OSError as exc:
            unreadable.append(f"{f.name}({type(exc).__name__})")
            continue
        read.append(f.name)
    return (total if read else None), read, unreadable


def main(argv: list[str]) -> int:
    if not argv or argv[0] in {"-h", "--help"}:
        print(__doc__.split("Usage:")[1].split("\n")[0].strip())
        return 2
    out_root = Path(argv[0]).expanduser().resolve()
    pattern = re.compile(UNGRACEFUL_DEFAULT)
    if "--pattern" in argv:
        pattern = re.compile(argv[argv.index("--pattern") + 1])

    legs_path = out_root / "legs.jsonl"
    if not legs_path.is_file():
        print(f"no legs.jsonl under {out_root}", file=sys.stderr)
        return 2
    legs = read_jsonl(legs_path)

    service_runs: list[tuple[int, Path, float]] = []
    for leg in legs:
        if leg.get("arm") != "service":
            continue
        suite_dir = Path(leg["suite_dir"])
        registry = suite_dir / "registry.jsonl"
        if not registry.is_file():
            print(f"pair {leg['pair']}: service suite {suite_dir} has no registry.jsonl", file=sys.stderr)
            return 2
        for row in read_jsonl(registry):
            service_runs.append((int(leg["pair"]), Path(row["run_dir"]), float(leg.get("load1", -1))))

    # cli-[0-9]*, NOT cli-*: sibling dirs such as cli-snapshots-from-worktree (the copied-out
    # .h5 preserve root) carry no logs, and a bare cli-* glob listed them as extra "legs"
    # reading 0 ungraceful stops -- a zero from a directory that was never a leg.
    cli_dirs = sorted(p for p in out_root.glob("cli-[0-9]*") if p.is_dir())
    cli_load = {int(leg["pair"]): float(leg.get("load1", -1)) for leg in legs if leg.get("arm") == "cli"}

    print(f"# G4 post-fix analysis for {out_root}")
    print(f"# provenance: {(out_root / 'provenance.json').read_text(encoding='utf-8').strip() if (out_root / 'provenance.json').is_file() else 'n/a'}")
    print(f"# service legs (resolved from this campaign's legs.jsonl -> registry.jsonl): {len(service_runs)}; CLI legs: {len(cli_dirs)}")
    for pair, run_dir, load in service_runs:
        print(f"#   service pair {pair}: {run_dir}  (load1 at launch {load})")
    for i, d in enumerate(cli_dirs, start=1):
        print(f"#   cli     pair {i}: {d}  (load1 at launch {cli_load.get(i, 'n/a')})")
    print()

    print("## ungraceful worker stops per leg (the acceptance discriminator)")
    print(f"pattern: /{pattern.pattern}/ counted across logs/juniper_cascor.log* (rotated siblings included)")
    cli_total = 0
    svc_total = 0
    gaps: list[str] = []
    for i, d in enumerate(cli_dirs, start=1):
        n, files, bad = count_in_logs(d / "logs", pattern)
        if n is None:
            gaps.append(f"cli pair {i}")
        else:
            cli_total += n
        print(f"  cli     pair {i}: {'n/a' if n is None else f'{n:3d}'}   files={files}" + (f"  UNREADABLE={bad}" if bad else ""))
    for pair, run_dir, _ in service_runs:
        n, files, bad = count_in_logs(run_dir / "logs", pattern)
        if n is None:
            gaps.append(f"service pair {pair}")
        else:
            svc_total += n
        print(f"  service pair {pair}: {'n/a' if n is None else f'{n:3d}'}   files={files}" + (f"  UNREADABLE={bad}" if bad else ""))
    print(f"  TOTAL cli={cli_total} service={svc_total}")
    if gaps:
        # Never let a silent gap read as a clean sweep: the total above is over the legs that
        # actually produced a readable log, and these did not.
        print(f"  !! {len(gaps)} leg(s) produced NO readable log and are EXCLUDED from the total: {', '.join(gaps)}")
        print("  !! The totals above are NOT a full-campaign result until those legs are explained.")
    print()

    if not DECOMPOSER.is_file():
        print(f"decomposer missing: {DECOMPOSER}", file=sys.stderr)
        return 2
    cmd = [sys.executable, str(DECOMPOSER), "--dir-arm", "cli", str(out_root)]
    if service_runs:
        cmd += ["--run-arm", "service", *[str(r) for _, r, _ in service_runs]]
    print("## decomposition")
    print("$ " + " ".join(cmd))
    # Fixed interpreter (sys.executable) + ledger-derived paths; no shell.
    proc = subprocess.run(cmd, check=False, capture_output=True, text=True)  # nosec B603
    sys.stdout.write(proc.stdout)
    if proc.stderr.strip():
        sys.stdout.write("\n[decomposer stderr]\n" + proc.stderr)
    print(f"\n# decomposer exit {proc.returncode}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
