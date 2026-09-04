#!/usr/bin/env python3
r"""Run one soak probe end to end: dispatch, execute, capture evidence, score-prep.

Project:     Juniper
Sub-Project: juniper-ml
Application: util
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Automates the mechanical parts of a pointer-follow soak run so the only thing
left to a human is the judgement the protocol reserves for one.

Why this is possible at all, when three other instruments were rejected
----------------------------------------------------------------------
`notes/JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md` §17 and §19
rule out three ways of running a probe, each because the instrument cannot see
the intervention being measured:

  * subagents      -- memory context is a snapshot frozen at PARENT session start
  * cloud routines -- no `MEMORY.md` in the sandbox at all
  * CronCreate     -- fires into the scheduling session, which is primed

Those sections then generalised to "the re-soak is operator-dispatched, not
automated". That generalisation was too broad. A **local headless `claude -p`
invocation** is a fourth mechanism and it satisfies every requirement, measured
2026-09-01:

    {"port_check_fail_opens": true, "per_run_timeout_ordering": true,
     "reaper_over_protects": true, "diverging_worktree_converge": true,
     "last_row_title": "ps cmdline leaks the aescrypt passphrase"}

All four rung-1 rows visible, and a row added by a peer AFTER them -- so the
snapshot is live at invocation, not merely post-intervention. It is a fresh
session (new id), it is local (so the index exists), and it is unprimed provided
it is handed the task and nothing else, which is what this script guarantees.

What is automated and what is NOT
---------------------------------
Automated, because it is mechanical:
  * probe selection (least-covered first -- choosing is a way to bias the sample)
  * dispatch of the bare task, with no preamble of any kind
  * capture of the transcript and every tool call
  * the RETRIEVAL CHANNEL: did the run read the probe's pointer document, or did
    it reach the fact from source? That is a file-path question, not a judgement.

NOT automated, deliberately:
  * whether the answer is CORRECT against the frozen discriminator.

That last one is judgement, and a wrapper that guessed it would be scoring its
own experiment. The script emits a scoring packet and stops. `soak_ledger.py
probe-run` still needs a human or a separate session to supply `--outcome`.

The reaper hazard, stated correctly
-----------------------------------
`AGENTS.md` § Hazards: `util/reap_pytest_orphans.bash` treats reparenting to
`systemd --user` as its orphan predicate. But being an orphan is only the SECOND
half of the test. The candidate filter comes first, verbatim from
`util/reap_pytest_orphans.bash:161`:

    $2 == me && /python/ && (/JuniperC[a-z0-9]+/ || /Juniper\/worktrees\//)

It matches CMDLINE TEXT and never inspects cwd -- `ps` reports argv, not the
working directory. So where the wrapper runs from grants no immunity in either
direction; the interpreter path decides it. `/usr/bin/python3` matches neither
alternative and is not a candidate at all; a `JuniperC*` conda interpreter is a
candidate from the identical directory.

An earlier version of this docstring claimed immunity followed from running in
the primary checkout. That was wrong -- cwd is structurally invisible to the
filter -- and it mattered, because it would have made a conda-interpreter
invocation look safe when it is not.

The guard below is therefore defence for the case that filter does catch. It
must be written where the reaper actually LOOKS: `collect_protected_pids`
(`:93-105`) walks only `$JUNIPER_EXP_RUN_ROOT` and `$JUNIPER_E2E_RUN_DIR`, so a
pidfile under `reports/soak/runs/` -- as the first version wrote -- is never
read and grants nothing. A killed probe is not a miss; it is a lost run.

Usage:
    python3 util/soak_run_probe.py                     # least-covered probe
    python3 util/soak_run_probe.py --probe-id P19-port-check-fail-opens
    python3 util/soak_run_probe.py --background        # detach; poll the run dir
    python3 util/soak_run_probe.py --dry-run           # show what would run

Exit codes:
    0  probe ran, scoring packet written
    1  probe ran but produced no usable answer (timeout, empty, error result)
    2  misuse, or the harness itself failed before the probe started
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess  # nosec B404 - fixed argv, no shell
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DISPATCH = ROOT / "util" / "soak_next_probe.py"
LEDGER_TOOL = ROOT / "util" / "soak_ledger.py"
RUNS = ROOT / "reports" / "soak" / "runs"
DEFAULT_TIMEOUT = 900


def claude_search_paths(home: Path | None = None) -> tuple[Path, ...]:
    """Fallbacks when PATH does not contain `claude` (systemd --user / cron)."""
    h = Path.home() if home is None else home
    return (h / ".local/bin/claude", Path("/usr/local/bin/claude"))


def resolve_claude(
    home: Path | None = None,
    search_paths: tuple[Path, ...] | None = None,
) -> str:
    """Absolute path to the `claude` binary, or exit 2 saying so.

    NOT `Popen(["claude", ...])`. `subprocess` resolves a bare name against the
    PATH in the env dict it is HANDED, and every unattended launcher hands it a
    minimal one. Measured on this host:

        systemctl --user show-environment | grep ^PATH=
        PATH=/home/pcalnon/.cargo/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:
             /usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin

    `claude` lives in ~/.local/bin, which is NOT on it, so a bare name raises
    FileNotFoundError before the probe starts. cron's environment is smaller
    still. The first version of this script had exactly that bug, and it was
    silent in the worst way: the run directory is created first, so each firing
    left task.txt and meta.json with no status.json -- debris that reads like a
    crashed probe rather than a launcher that never launched.
    """
    found = shutil.which("claude")
    if found:
        return found
    for cand in claude_search_paths(home) if search_paths is None else search_paths:
        if cand.is_file() and os.access(cand, os.X_OK):
            return str(cand)
    raise SystemExit(
        "cannot find the `claude` binary. PATH as seen by this process:\n"
        f"  {os.environ.get('PATH', '(unset)')}\n"
        "Under systemd --user or cron this is expected: ~/.local/bin is not on the "
        "default PATH. Set Environment=PATH=... in the unit, or install claude on "
        "a system path."
    )


def reaper_guard_path(pid: int, exp_run_root: str | None = None, home: Path | None = None) -> Path:
    """Pidfile path the orphan reaper actually scans.

    `collect_protected_pids` in `util/reap_pytest_orphans.bash` walks only
    `$JUNIPER_EXP_RUN_ROOT` and `$JUNIPER_E2E_RUN_DIR`. A pidfile under
    `reports/soak/runs/` is never read and grants nothing. The first version of
    this wrapper wrote exactly that, so it looked like a mitigation while
    protecting zero probes.
    """
    if exp_run_root is None:
        root = (home if home is not None else Path.home()) / ".local/state/juniper-experiments"
    else:
        root = Path(exp_run_root)
    return root / "soak-probes" / f"soak-probe-{int(pid)}.pid"


def probe_child_env(base: dict[str, str] | None = None) -> dict[str, str]:
    """Env handed to the subject session.

    A stale `ANTHROPIC_API_KEY` with no credit fails the run with
    "Credit balance is too low" before the probe ever starts. Subscription auth
    is what the unattended path uses.
    """
    env = dict(os.environ if base is None else base)
    env.pop("ANTHROPIC_API_KEY", None)
    return env


def timeout_status(
    probe_id: str,
    session_id: str,
    timeout_s: int,
    stderr_tail: str | None,
    ended_at: str,
) -> dict:
    """Status written when the subject is killed for wall-clock.

    An earlier version bound `err` here and dropped it. A timeout is precisely
    when the child's last words are worth having, and the status file is the
    only place they can be read afterwards.
    """
    return {
        "probe_id": probe_id,
        "session_id": session_id,
        "state": "TIMEOUT",
        "timeout_s": timeout_s,
        "ended_at": ended_at,
        "stderr_tail": (stderr_tail or "")[-400:],
    }


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _py(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(  # nosec B603
        [sys.executable, *args], cwd=cwd or ROOT, capture_output=True, text=True, timeout=120
    )


def dispatch(probe_id: str | None) -> tuple[str, str]:
    """Return (probe_id, task). The task is never logged to stdout by this step."""
    args = [str(DISPATCH)]
    if probe_id:
        args += ["--probe-id", probe_id]
    p = _py(*args)
    if p.returncode != 0:
        raise SystemExit(f"dispatch failed rc={p.returncode}: {p.stderr.strip()[:300]}")
    task = p.stdout.strip()
    if not task:
        raise SystemExit("dispatch produced an empty task")
    # The probe id is on stderr by design, so stdout stays paste-clean.
    pid_line = next((ln for ln in p.stderr.splitlines() if ln.startswith("# probe ")), "")
    resolved = pid_line.split()[2] if pid_line else (probe_id or "UNKNOWN")
    return resolved, task


def parse_events(path: Path) -> dict:
    """Pull the answer and every tool-visible file path out of a stream-json log."""
    answer, tools, files, errors = [], [], [], []
    result_meta: dict = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        etype = ev.get("type")
        if etype == "result":
            result_meta = {
                k: ev.get(k) for k in ("subtype", "is_error", "duration_ms", "num_turns", "session_id")
            }
            if isinstance(ev.get("result"), str):
                answer.append(ev["result"])
        # `message` is not always an object. Some stream-json events carry it as a
        # bare string, and `ev.get("message") or {}` happily yields that string --
        # then `.get` on it raises AttributeError and the whole run is lost at the
        # parse step, AFTER the session has been spent. Guard the type, not just
        # the absence.
        msg = ev.get("message")
        if not isinstance(msg, dict):
            continue
        content = msg.get("content")
        for block in content if isinstance(content, list) else []:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "text" and etype == "assistant":
                answer.append(block.get("text", ""))
            if block.get("type") == "tool_use":
                name = block.get("name", "")
                inp = block.get("input", {}) or {}
                tools.append(name)
                blob = json.dumps(inp)
                files.append(blob)
                if name.lower() in {"bash"} and "error" in blob.lower():
                    errors.append(blob[:200])
    return {
        "answer": "\n".join(a for a in answer if a).strip(),
        "tool_calls": tools,
        "tool_inputs": files,
        "result": result_meta,
        "errors": errors,
    }


def retrieval_channel(parsed: dict, pointer: str) -> dict:
    """Mechanical: did the run touch the pointer document, or only source?

    This is the follow / source-recovered distinction, and it is a file-path
    question rather than a judgement -- which is exactly why it is safe to
    automate while correctness is not.
    """
    doc = pointer.split("#", 1)[0].strip() if pointer else ""
    blob = "\n".join(parsed["tool_inputs"]) + "\n" + parsed["answer"]
    hit = bool(doc) and doc in blob
    return {
        "pointer_doc": doc,
        "pointer_doc_referenced": hit,
        "suggests": "follow" if hit else "source-recovered-or-miss",
        "note": (
            "MECHANICAL ONLY. A pointer hit means the document was reached, not that "
            "the answer is correct; an absence means it was not, which is consistent "
            "with BOTH source-recovered (correct) and miss (wrong). Correctness "
            "against the frozen discriminator is a judgement this script does not make."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe-id", default=None)
    ap.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    ap.add_argument("--background", action="store_true", help="detach; poll the run dir")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true",
                    help="run even when the soak verdict is terminal")
    ap.add_argument("--notify-cmd", default=None,
                    help="shell-free command run on completion; the run dir is appended as argv")
    args = ap.parse_args()

    # STOPPING RULE. Nothing else in the dispatch path consults the verdict, so
    # without this an enabled timer keeps spending real Claude sessions forever --
    # including after the soak has already reached a terminal answer, which is
    # spend that cannot change a conclusion. Adversarial review raised this as a
    # blocking gap in the unattended (systemd) path specifically.
    terminal = ("BET-FAILING", "HOLDS-AT-")
    st = _py(str(LEDGER_TOOL), "status")
    verdict = (st.stdout.split() or [""])[0]
    if any(verdict.startswith(t) for t in terminal) and not args.force:
        print(f"REFUSING: soak verdict is {verdict} -- terminal. Further runs cannot "
              f"change it and each one spends a session.\nPass --force to override "
              f"(e.g. to re-baseline after a deliberate intervention).", file=sys.stderr)
        return 2

    probe_id, task = dispatch(args.probe_id)
    session_id = str(uuid.uuid4())
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    run_dir = RUNS / f"{stamp}-{probe_id}"

    # Resolve LAZILY, after the dry-run branch. Building the command eagerly made
    # --dry-run require the `claude` binary, so on any machine without it (every
    # CI runner) the dry run exited 1 with empty stdout instead of describing what
    # it would do. A dry run must not depend on the thing it is only describing.
    if args.dry_run:
        print(f"probe    : {probe_id}")
        print(f"session  : {session_id}")
        print(f"run dir  : {run_dir}")
        print(f"timeout  : {args.timeout}s")
        try:
            binary = resolve_claude()
        except SystemExit:
            binary = "NOT FOUND on this PATH (fine for a dry run; fatal for a real one)"
        print(f"claude   : {binary}")
        print("command  : <claude> -p <task> --output-format stream-json --verbose --session-id <uuid>")
        print("\nThe task is NOT printed here: this script's own stdout is read by operators,")
        print("and echoing the task where a scorer can see it is how priming leaks back in.")
        return 0

    cmd = [
        resolve_claude(), "-p", task,
        "--output-format", "stream-json",
        "--verbose",
        "--session-id", session_id,
    ]

    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "task.txt").write_text(task + "\n", encoding="utf-8")
    (run_dir / "meta.json").write_text(json.dumps({
        "probe_id": probe_id, "session_id": session_id, "started_at": _now(),
        "timeout_s": args.timeout, "cwd": str(ROOT),
    }, indent=2) + "\n", encoding="utf-8")

    log = run_dir / "stream.jsonl"
    env = probe_child_env()

    with log.open("w", encoding="utf-8") as fh:
        proc = subprocess.Popen(  # nosec B603
            cmd, cwd=ROOT, stdout=fh, stderr=subprocess.PIPE, text=True,
            env=env, stdin=subprocess.DEVNULL,
            start_new_session=args.background,
        )
        # Reaper protection key #1, written BEFORE the child can be reparented.
        #
        # It must go in a directory the reaper actually SCANS. `collect_protected_pids`
        # in util/reap_pytest_orphans.bash walks only $JUNIPER_EXP_RUN_ROOT and
        # $JUNIPER_E2E_RUN_DIR (`find <root> -maxdepth 3 -name '*.pid'`). The first
        # version of this wrapper wrote the pidfile into reports/soak/runs/ inside the
        # repo -- in neither root -- so it granted ZERO protection while reading like
        # a mitigation. A protection artifact that does not protect is worse than an
        # acknowledged gap, because it stops anyone looking again.
        #
        # The run-dir copy is kept as well: it is what an operator polls, and it is
        # the second documented protection key (a cmdline referencing a run root)
        # for anything that reads it.
        (run_dir / f"probe-{proc.pid}.pid").write_text(f"{proc.pid}\n", encoding="utf-8")
        guard = reaper_guard_path(proc.pid, os.environ.get("JUNIPER_EXP_RUN_ROOT"))
        try:
            guard.parent.mkdir(parents=True, exist_ok=True)
            guard.write_text(f"{proc.pid}\n", encoding="utf-8")
            (run_dir / "reaper_guard_path.txt").write_text(str(guard) + "\n", encoding="utf-8")
        except OSError as exc:
            # Loud, not silent: an unprotected probe can be reaped mid-run, and a
            # reaped probe is not a miss -- it is a lost run that would have scored.
            print(f"WARNING: could not write reaper guard under {guard.parent}: {exc}",
                  file=sys.stderr)
        if args.background:
            print(f"probe {probe_id} detached: pid {proc.pid}, run dir {run_dir}")
            print("Poll status.json; the pidfile protects it from the orphan reaper.")
            return 0
        try:
            _, err = proc.communicate(timeout=args.timeout)
        except subprocess.TimeoutExpired:
            # kill() reaps only the direct child. If `claude` spawned tool
            # subprocesses that inherited the stderr pipe, they hold it open and
            # a bare communicate() with no timeout blocks forever -- the wrapper
            # then hangs past TimeoutStartSec and systemd cgroup-kills the unit
            # BEFORE status.json is written, producing exactly the "crash, not
            # timeout" outcome the 900/1200 split exists to prevent.
            proc.kill()
            try:
                _, err = proc.communicate(timeout=30)
            except subprocess.TimeoutExpired:
                err = "(stderr unreadable: child or its descendants held the pipe open)"
            # Record the captured stderr. An earlier version bound `err` here and
            # dropped it -- CodeQL flagged the unused variable, and it was a real
            # defect rather than a lint nit: a timeout is precisely when the
            # child's last words are worth having, and the status file was the
            # only place they could have been read afterwards.
            (run_dir / "status.json").write_text(json.dumps(
                timeout_status(probe_id, session_id, args.timeout, err, _now()),
                indent=2,
            ) + "\n", encoding="utf-8")
            print(f"TIMEOUT after {args.timeout}s -- run dir {run_dir}", file=sys.stderr)
            return 1

    parsed = parse_events(log)
    reveal = _py(str(DISPATCH), "--reveal", "--probe-id", probe_id)
    pointer = ""
    for ln in reveal.stdout.splitlines():
        if ln.startswith("pointer"):
            pointer = ln.split(":", 1)[1].strip()
    channel = retrieval_channel(parsed, pointer)

    # REDACTION. `--reveal` prints a "post-interv. : N run(s)" coverage line, and an
    # earlier version embedded its stdout verbatim in the scoring packet -- so the
    # supposedly isolated scorer read a coverage number sitting beside the
    # discriminator. The whole point of separating the scorer from the orchestrator
    # is that the scorer has no stake in how the corpus is progressing; handing it
    # the tally defeats that in the one artifact built to implement it.
    scorer_reveal = "".join(
        ln + "\n" for ln in reveal.stdout.splitlines()
        if not ln.startswith("post-interv.")
    )

    ok = bool(parsed["answer"]) and not parsed["result"].get("is_error")
    status = {
        "probe_id": probe_id,
        "session_id": session_id,
        "state": "COMPLETE" if ok else "NO_ANSWER",
        "ended_at": _now(),
        "result": parsed["result"],
        "tool_call_count": len(parsed["tool_calls"]),
        "retrieval": channel,
        "stderr_tail": (err or "")[-400:],
    }
    (run_dir / "status.json").write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    (run_dir / "answer.md").write_text(parsed["answer"] + "\n", encoding="utf-8")
    (run_dir / "scoring_packet.md").write_text(
        f"# Scoring packet -- {probe_id}\n\n"
        f"session: `{session_id}`\nrun dir: `{run_dir}`\n\n"
        f"## Discriminator, pointer and fact (from --reveal)\n\n```\n{scorer_reveal}```\n\n"
        f"## Mechanical retrieval channel\n\n```json\n{json.dumps(channel, indent=2)}\n```\n\n"
        f"## The run's answer\n\n{parsed['answer']}\n\n"
        f"## Record it\n\n```bash\npython3 util/soak_ledger.py probe-run \\\n"
        f"    --probe-id {probe_id} \\\n"
        f"    --outcome follow|source-recovered|miss \\\n"
        f"    --session {session_id} --scored-by <who>\n```\n\n"
        "Correctness against the discriminator is NOT decided here. The retrieval\n"
        "channel above distinguishes follow from source-recovered; whether the answer\n"
        "is right is the judgement the protocol reserves for a scorer.\n",
        encoding="utf-8",
    )

    if args.notify_cmd:
        subprocess.run([args.notify_cmd, str(run_dir)], check=False)  # nosec B603

    print(f"{status['state']}  {probe_id}  session={session_id}")
    print(f"  pointer doc referenced : {channel['pointer_doc_referenced']}  ({channel['suggests']})")
    print(f"  tool calls             : {len(parsed['tool_calls'])}")
    print(f"  scoring packet         : {run_dir / 'scoring_packet.md'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
