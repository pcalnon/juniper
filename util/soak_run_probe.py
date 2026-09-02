#!/usr/bin/env python3
"""Run one soak probe end to end: dispatch, execute, capture evidence, score-prep.

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

The reaper hazard
-----------------
`AGENTS.md` § Hazards: `util/reap_pytest_orphans.bash` treats reparenting to
`systemd --user` as its orphan predicate, so anything launched under `nohup` --
including a backgrounded probe -- is a reap candidate. Two protection keys exist
and either suffices; this writes the first, a `*.pid` in the run directory,
BEFORE the child can be reparented. Without it a `--background` run is liable to
be killed mid-probe by an unrelated sweep, and a killed probe is not a miss.

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
        msg = ev.get("message") or {}
        for block in msg.get("content", []) if isinstance(msg.get("content"), list) else []:
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
    ap.add_argument("--notify-cmd", default=None,
                    help="shell-free command run on completion; the run dir is appended as argv")
    args = ap.parse_args()

    probe_id, task = dispatch(args.probe_id)
    session_id = str(uuid.uuid4())
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    run_dir = RUNS / f"{stamp}-{probe_id}"

    cmd = [
        "claude", "-p", task,
        "--output-format", "stream-json",
        "--verbose",
        "--session-id", session_id,
    ]

    if args.dry_run:
        print(f"probe    : {probe_id}")
        print(f"session  : {session_id}")
        print(f"run dir  : {run_dir}")
        print(f"timeout  : {args.timeout}s")
        print("command  : claude -p <task> --output-format stream-json --verbose --session-id <uuid>")
        print("\nThe task is NOT printed here: this script's own stdout is read by operators,")
        print("and echoing the task where a scorer can see it is how priming leaks back in.")
        return 0

    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "task.txt").write_text(task + "\n", encoding="utf-8")
    (run_dir / "meta.json").write_text(json.dumps({
        "probe_id": probe_id, "session_id": session_id, "started_at": _now(),
        "timeout_s": args.timeout, "cwd": str(ROOT),
    }, indent=2) + "\n", encoding="utf-8")

    log = run_dir / "stream.jsonl"
    env = dict(os.environ)
    # Subscription auth: a stale ANTHROPIC_API_KEY with no credit fails the run
    # with "Credit balance is too low" before the probe ever starts.
    env.pop("ANTHROPIC_API_KEY", None)

    with log.open("w", encoding="utf-8") as fh:
        proc = subprocess.Popen(  # nosec B603
            cmd, cwd=ROOT, stdout=fh, stderr=subprocess.PIPE, text=True,
            env=env, stdin=subprocess.DEVNULL,
            start_new_session=args.background,
        )
        # Reaper protection key #1, written BEFORE the child can be reparented.
        (run_dir / f"probe-{proc.pid}.pid").write_text(f"{proc.pid}\n", encoding="utf-8")
        if args.background:
            print(f"probe {probe_id} detached: pid {proc.pid}, run dir {run_dir}")
            print("Poll status.json; the pidfile protects it from the orphan reaper.")
            return 0
        try:
            _, err = proc.communicate(timeout=args.timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            _, err = proc.communicate()
            (run_dir / "status.json").write_text(json.dumps({
                "probe_id": probe_id, "session_id": session_id, "state": "TIMEOUT",
                "timeout_s": args.timeout, "ended_at": _now(),
            }, indent=2) + "\n", encoding="utf-8")
            print(f"TIMEOUT after {args.timeout}s -- run dir {run_dir}", file=sys.stderr)
            return 1

    parsed = parse_events(log)
    reveal = _py(str(DISPATCH), "--reveal", "--probe-id", probe_id)
    pointer = ""
    for ln in reveal.stdout.splitlines():
        if ln.startswith("pointer"):
            pointer = ln.split(":", 1)[1].strip()
    channel = retrieval_channel(parsed, pointer)

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
        f"## Discriminator, pointer and fact (from --reveal)\n\n```\n{reveal.stdout}```\n\n"
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
