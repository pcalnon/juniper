#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Measure the *tail-flush latency* of Duplicati's GPG encryption pipeline -- the
exact quantity that ``GPGStreamWrapper.Dispose`` bounds with ``m_t.Join(5000)``
-- under controlled load regimes.

Why this exists
---------------
The 2026-08-23 fresh-backup run 2 died with ``CryptographicException: Failure
while invoking GnuPG, program won't flush output``.  Source inspection of the
installed version (Duplicati 2.3.0.4, tag ``v2.3.0.4_stable_2026-07-09``,
``Duplicati/Library/Encryption/GPGStreamWrapper.cs``) shows that exception is
thrown when a pump thread copying ``gpg`` stdout to the ciphertext file fails
to finish within a **hardcoded 5000 ms** of the plaintext stream being closed:

    m_basestream.Close();                 // closes gpg stdin -> EOF
    if (!m_t.Join(5000))                  // pump: gpg stdout -> output file
        throw ... GPGFlushError           // "program won't flush output"
    if (!m_p.WaitForExit(5000))
        throw ... GPGTerminateError

At stdin-close, gpg's remaining work is small (zlib flush + MDC trailer), so
the bound is only blown when that tail work *cannot get scheduled* or its
writes stall: CPU starvation (the failing run was Nice=10 under systemd with
default 16-way Duplicati concurrency) or dirty-page writeback throttling on a
saturated disk.  The predecessor session's throughput probe
(``duplicati_gpg_throughput.bash``) measured one solo, foreground, idle
invocation -- structurally blind to both mechanisms.  This script measures the
tail itself, in regime.

Pipeline fidelity (mirrors GPGEncryption.Execute for the encrypt path)
----------------------------------------------------------------------
* argv:  ``gpg --batch --passphrase-fd 0 --symmetric``  (the job overrides
  nothing: no ``--gpg-encryption-switches`` in the fresh job or the runner)
* passphrase written as the first stdin line, then ``Thread.Sleep(1000)`` and
  a HasExited check, then a dedicated pump thread copies stdout -> file while
  the caller feeds plaintext -> stdin, then stdin is closed.
* chunk size 64 KiB both directions (assumption: Duplicati's CopyStream buffer;
  tail semantics do not depend on it).
* stderr is a pipe left undrained until exit, as in Duplicati.
* ``--nice`` applies the niceness to the gpg process AND both pipeline threads
  (feeder + pump) via per-thread setpriority, matching a whole-process Nice=10
  service.  Load workers stay at nice 0, matching run 2's position as the
  *nicest* work on the box.  ``--ionice`` wraps gpg with ``ionice -c2 -n7``
  (pump-thread writeback priority is kernel-side and not reproduced -- noted
  limitation).

Reported per trial
------------------
* TAIL_JOIN  = t(pump saw EOF and closed output) - t(stdin closed)   [Join bound]
* TAIL_EXIT  = t(gpg exited) - t(stdin closed)                       [WaitForExit bound]
* BOUND_5S   = OK | EXCEEDED | HANG (watchdog)
* gpg CPU seconds (utime+stime sampled from /proc), max PSI avg10
  (cpu/io/memory, sampled every 500 ms *during* the trial -- PSI decays).

Safety
------
Writes only inside ``--workdir`` (default
``/media/pcalnon/temp_backups/_gpg_repro/micro``); refuses a workdir inside
either real backup destination; uses a literal scratch passphrase; never
touches Duplicati, its databases, or the credential files.  Load workers are
children of this process and are terminated in ``finally``.
"""

import argparse
import math
import os
import subprocess
import sys
import threading
import time

CHUNK = 64 * 1024
SCRATCH_PASSPHRASE = "gpg-tail-latency-scratch-passphrase"
FORBIDDEN_WORKDIR_PREFIXES = (
    "/media/pcalnon/temp_backups/Ubuntu",
    "/mnt/Backups",
    "/home/pcalnon/.config/Duplicati",
    "/home/pcalnon/.config/duplicati-backup",
)
PSI_FILES = {p: f"/proc/pressure/{p}" for p in ("cpu", "io", "memory")}


def read_psi():
    """Return {resource: (some_avg10, some_total_us)} for cpu/io/memory."""
    out = {}
    for name, path in PSI_FILES.items():
        try:
            with open(path) as fh:
                # first line: "some avg10=X avg60=Y avg300=Z total=N"  (N in us)
                first = fh.readline().split()
                out[name] = (float(first[1].split("=")[1]), int(first[4].split("=")[1]))
        except (OSError, IndexError, ValueError):
            out[name] = (float("nan"), 0)
    return out


def set_thread_nice(nice):
    if nice:
        try:
            os.setpriority(os.PRIO_PROCESS, threading.get_native_id(), nice)
        except OSError as exc:  # pragma: no cover - diagnostic only
            print(f"WARN: could not set thread nice: {exc}", file=sys.stderr)


class PsiSampler(threading.Thread):
    """Track max avg10 AND total-counter deltas (stall seconds) over a window.

    avg10 is a 10 s EMA that under-detects 2-5 s stalls; the total= counter is
    cumulative stall time in us and catches them exactly.
    """

    def __init__(self):
        super().__init__(daemon=True)
        self.stop_event = threading.Event()
        self.max_avg10 = {k: 0.0 for k in PSI_FILES}
        self.start_total = {k: v[1] for k, v in read_psi().items()}
        self.end_total = dict(self.start_total)

    def run(self):
        while not self.stop_event.wait(0.5):
            for k, (avg, total) in read_psi().items():
                if not math.isnan(avg) and avg > self.max_avg10[k]:  # NaN-safe
                    self.max_avg10[k] = avg
                self.end_total[k] = total

    def stall_seconds(self, key):
        return (self.end_total[key] - self.start_total[key]) / 1e6


class GpgStatSampler(threading.Thread):
    """Sample /proc/<pid>/stat for gpg: cumulative CPU ticks and last state."""

    def __init__(self, pid):
        super().__init__(daemon=True)
        self.pid = pid
        self.stop_event = threading.Event()
        self.cpu_ticks = 0
        self.last_state = "?"

    def run(self):
        while not self.stop_event.wait(0.1):
            try:
                with open(f"/proc/{self.pid}/stat") as fh:
                    fields = fh.read().rsplit(")", 1)[1].split()
                # after the comm field: fields[0]=state, utime=fields[11], stime=fields[12]
                self.last_state = fields[0]
                self.cpu_ticks = int(fields[11]) + int(fields[12])
            except (OSError, IndexError, ValueError):
                return


class Pipeline:
    """One gpg encrypt pipeline, wired the way Duplicati wires it."""

    def __init__(self, idx, input_path, workdir, nice, ionice, gpg_extra, watchdog_s, stagger_s):
        self.idx = idx
        self.input_path = input_path
        self.out_path = os.path.join(workdir, f"out-{idx}.gpg")
        self.nice = nice
        self.watchdog_s = watchdog_s
        self.stagger_s = stagger_s
        # nice/ionice as argv prefixes: preexec_fn is unsafe with threads
        # (fork-with-threads hazard under --parallel).
        argv = []
        if nice:
            argv += ["nice", "-n", str(nice)]
        if ionice:
            argv += ["ionice", "-c2", "-n7"]  # no-op on mq-deadline; kept for unit parity
        argv += ["gpg", "--batch", "--passphrase-fd", "0"]
        if gpg_extra:
            # Duplicati places extra switches BEFORE the command
            argv += gpg_extra.split()
        argv += ["--symmetric"]
        self.argv = argv
        self.result = {}
        self.t_close = None
        self.t_eof = None
        self.t_gpg_exit = None
        self.pump_exc = None

    def _pump(self, stdout, outfile):
        set_thread_nice(self.nice)
        try:
            while True:
                data = stdout.read(CHUNK)
                if not data:
                    break
                outfile.write(data)
            outfile.close()
            # stamped AFTER close: Duplicati's pump thread ends after closing the
            # output stream, and a stall in the final close-flush must count.
            self.t_eof = time.monotonic()
        except Exception as exc:  # noqa: BLE001 - recorded, not raised
            self.pump_exc = exc

    def _exit_waiter(self, proc):
        # Independent observer of gpg's actual exit time: under a starved pump,
        # gpg can exit long before the pump drains -- stamping exit at
        # pump-join-return would misattribute a pump stall to gpg termination.
        try:
            proc.wait()
            self.t_gpg_exit = time.monotonic()
        except Exception:  # noqa: BLE001 - observer only
            pass

    def run(self):
        if self.stagger_s:
            time.sleep(self.stagger_s * self.idx)
        proc = subprocess.Popen(
            self.argv,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stat = GpgStatSampler(proc.pid)
        stat.start()
        waiter = threading.Thread(target=self._exit_waiter, args=(proc,), daemon=True)
        waiter.start()
        outfile = None
        pump = None
        try:
            outfile = open(self.out_path, "wb")
            proc.stdin.write((SCRATCH_PASSPHRASE + "\n").encode())
            proc.stdin.flush()
            time.sleep(1.0)  # Duplicati: Thread.Sleep(1000)
            if proc.poll() is not None:
                raise RuntimeError(f"gpg exited early: {proc.stderr.read()!r}")

            pump = threading.Thread(target=self._pump, args=(proc.stdout, outfile))
            pump.start()

            set_thread_nice(self.nice)  # the feeder thread (this one)
            t_feed_start = time.monotonic()
            fed = 0
            with open(self.input_path, "rb") as src:
                while True:
                    data = src.read(CHUNK)
                    if not data:
                        break
                    proc.stdin.write(data)
                    fed += len(data)
            proc.stdin.close()
            self.t_close = time.monotonic()

            pump.join(self.watchdog_s)
            hang = pump.is_alive()
            t_join_return = time.monotonic()
            if hang:
                proc.terminate()
                try:
                    proc.wait(10)
                except subprocess.TimeoutExpired:
                    proc.kill()
                try:
                    proc.wait(30)
                except subprocess.TimeoutExpired:
                    print("warning: gpg process did not exit within 30s after kill()", file=sys.stderr)
                pump.join(5)
            else:
                try:
                    proc.wait(self.watchdog_s)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(30)
            waiter.join(5)
            rc = proc.returncode
            stat.stop_event.set()

            tail_join = (self.t_eof - self.t_close) if self.t_eof else float("inf")
            # C#'s WaitForExit(5000) budget starts when Join RETURNS, and gpg's
            # true exit time comes from the independent waiter.
            if self.t_gpg_exit is not None:
                tail_exit = max(0.0, self.t_gpg_exit - t_join_return)
                exit_from_close = self.t_gpg_exit - self.t_close
            else:
                tail_exit = float("inf")
                exit_from_close = float("inf")
            # Only TAIL_JOIN > 5 s is the analog of the observed failure
            # (GPGFlushError = Join(5000) miss).  A dead pump makes C#'s Join
            # return TRUE (different signature), so it must not count as
            # EXCEEDED here either.
            if self.pump_exc is not None:
                verdict = "PUMP_DIED"
            elif hang:
                verdict = "HANG"
            elif tail_join > 5.0:
                verdict = "EXCEEDED"
            elif tail_exit > 5.0:
                verdict = "EXIT_EXCEEDED"
            else:
                verdict = "OK"
            self.result = {
                "pipeline": self.idx,
                "fed_mib": fed / 2**20,
                "feed_s": self.t_close - t_feed_start,
                "tail_join_s": tail_join,
                "tail_exit_s": tail_exit,
                "exit_from_close_s": exit_from_close,
                "gpg_cpu_s": stat.cpu_ticks / os.sysconf("SC_CLK_TCK"),
                "gpg_last_state": stat.last_state,
                "rc": rc,
                "out_bytes": os.path.getsize(self.out_path) if os.path.exists(self.out_path) else 0,
                "verdict": verdict,
                "pump_exc": repr(self.pump_exc) if self.pump_exc else "",
            }
        finally:
            stat.stop_event.set()
            # Close the output file only if the pump is not wedged in a write:
            # BufferedWriter.close() would block on the lock a stuck write holds.
            if outfile is not None and not outfile.closed and (pump is None or not pump.is_alive()):
                try:
                    outfile.close()
                except OSError as e:
                    if not self.pump_exc:
                        self.pump_exc = RuntimeError(f"outfile.close failed: {e!r}")
            for stream in (proc.stdin, proc.stdout, proc.stderr):
                try:
                    stream.close()
                except OSError:
                    pass
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(10)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    try:
                        proc.wait(30)
                    except subprocess.TimeoutExpired:
                        pass
            try:
                os.unlink(self.out_path)
            except OSError:
                pass
        return self.result


def spawn_worker(kind, arg=None):
    if kind == "cpu":
        src = (
            "import hashlib\n"
            "buf = b'x' * 65536\n"
            "while True:\n"
            "    hashlib.sha256(buf).digest()\n"
        )
        return subprocess.Popen([sys.executable, "-c", src])
    src = (
        "import os, sys\n"
        f"path = {arg!r}\n"
        "buf = os.urandom(1 << 20) * 64\n"
        "rotate = 4 * 2**30\n"
        "written = 0\n"
        "fh = open(path, 'wb')\n"
        "while True:\n"
        "    fh.write(buf)\n"
        "    written += len(buf)\n"
        "    if written % (512 * 2**20) == 0:\n"
        "        os.fsync(fh.fileno())\n"
        "    if written >= rotate:\n"
        "        fh.seek(0); written = 0\n"  # no truncate: keep the dirty set resident
    )
    return subprocess.Popen([sys.executable, "-c", src])


def build_input(path, size_mb):
    if os.path.exists(path) and os.path.getsize(path) == size_mb * 2**20:
        return
    print(f"building {size_mb} MiB incompressible input at {path} ...")
    with open(path, "wb") as fh:
        for _ in range(size_mb):
            fh.write(os.urandom(2**20))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[10])
    ap.add_argument("--workdir", default="/media/pcalnon/temp_backups/_gpg_repro/micro")
    ap.add_argument("--size-mb", type=int, default=500, help="plaintext size per pipeline (MiB)")
    ap.add_argument("--nice", type=int, default=0, help="niceness for gpg + pipeline threads (run 2 was 10)")
    ap.add_argument("--ionice", action="store_true", help="wrap gpg in ionice -c2 -n7 (run 2's class)")
    ap.add_argument("--cpu-load", type=int, default=0, help="N nice-0 CPU burner processes during the trial")
    ap.add_argument("--io-load", action="store_true", help="one writeback-pressure writer in workdir during the trial")
    ap.add_argument("--parallel", type=int, default=1, help="concurrent gpg pipelines (run 2 had 3 uploads in flight)")
    ap.add_argument("--trials", type=int, default=1)
    ap.add_argument("--gpg-extra", default="", help="extra gpg args, e.g. '-z 0'")
    ap.add_argument("--watchdog-s", type=float, default=900.0)
    ap.add_argument("--stagger-s", type=float, default=0.0, help="start pipeline i after i*stagger seconds (real volumes stagger)")
    args = ap.parse_args()

    workdir = os.path.realpath(args.workdir)
    for bad in FORBIDDEN_WORKDIR_PREFIXES:
        if workdir == bad or workdir.startswith(bad + "/"):
            sys.exit(f"REFUSED: workdir {workdir} is inside protected path {bad}")
    os.makedirs(workdir, exist_ok=True)

    input_path = os.path.join(workdir, f"input-{args.size_mb}mib.bin")
    build_input(input_path, args.size_mb)

    print(
        f"regime: nice={args.nice} ionice={args.ionice} cpu_load={args.cpu_load} "
        f"io_load={args.io_load} parallel={args.parallel} size={args.size_mb}MiB "
        f"gpg_extra={args.gpg_extra!r} trials={args.trials}"
    )
    workers = []
    try:
        for _ in range(args.cpu_load):
            workers.append(spawn_worker("cpu"))
        if args.io_load:
            workers.append(spawn_worker("io", os.path.join(workdir, "io-burner.bin")))
        if workers:
            time.sleep(3)  # let load establish before measuring

        for trial in range(1, args.trials + 1):
            psi = PsiSampler()
            psi.start()
            pipelines = [
                Pipeline(i, input_path, workdir, args.nice, args.ionice, args.gpg_extra, args.watchdog_s, args.stagger_s)
                for i in range(args.parallel)
            ]
            threads, results = [], [None] * len(pipelines)

            def make(i, p):
                def _run():
                    results[i] = p.run()
                return _run

            for i, p in enumerate(pipelines):
                t = threading.Thread(target=make(i, p))
                t.start()
                threads.append(t)
            for t in threads:
                t.join()
            psi.stop_event.set()
            psi.join(2)

            exceeded = 0
            for r in results:
                if r is None:
                    print(f"trial {trial}: pipeline produced no result (crashed)")
                    continue
                if r["verdict"] in ("EXCEEDED", "HANG"):
                    exceeded += 1
                print(
                    f"trial {trial} pipe {r['pipeline']}: "
                    f"feed {r['fed_mib']:.0f} MiB in {r['feed_s']:.2f}s | "
                    f"TAIL_JOIN {r['tail_join_s']:.3f}s TAIL_EXIT {r['tail_exit_s']:.3f}s "
                    f"(exit-from-close {r['exit_from_close_s']:.3f}s) | "
                    f"gpg_cpu {r['gpg_cpu_s']:.1f}s state {r['gpg_last_state']} rc {r['rc']} | "
                    f"out {r['out_bytes'] / 2**20:.0f} MiB | BOUND_5S: {r['verdict']}"
                    + (f" | pump_exc={r['pump_exc']}" if r["pump_exc"] else "")
                )
            print(
                "trial {} signature: {}/{} pipelines exceeded | PSI max avg10 cpu={:.1f} io={:.1f} mem={:.1f} | "
                "PSI stall-s over trial: cpu={:.1f} io={:.1f} mem={:.1f}".format(
                    trial, exceeded, len(pipelines),
                    psi.max_avg10["cpu"], psi.max_avg10["io"], psi.max_avg10["memory"],
                    psi.stall_seconds("cpu"), psi.stall_seconds("io"), psi.stall_seconds("memory"),
                )
            )
    finally:
        for w in workers:
            w.terminate()
        for w in workers:
            try:
                w.wait(10)
            except subprocess.TimeoutExpired:
                w.kill()
        burn = os.path.join(workdir, "io-burner.bin")
        if os.path.exists(burn):
            os.unlink(burn)


if __name__ == "__main__":
    main()
