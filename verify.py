#!/usr/bin/env python3
# Green check for the extra W2D5 lab (compose chaos drill).
# Run WITH the chaos stack up:  python verify.py
# Prints exactly one line last: GREEN CHECK: PASS  or  GREEN CHECK: FAIL (<reason>)
# stdlib only. Takes ~60 seconds: it is a live drill, not a file check.
#
# Two conditions, both required:
#   1. client-observed uptime >= 95% over the window (this verifier's own poll,
#      not the student's uptime_report.json)
#   2. the serving container restarted >= MIN_RESTARTS times during the window,
#      read from Docker itself. This is the anti-cheat: an uptime target met by
#      quietly slowing the chaos interval down is not the drill.
import os, subprocess, time, urllib.request
from typing import NoReturn

BASE = os.environ.get("BASE_URL", "http://localhost:8000").rstrip("/")
TARGET = os.environ.get("TARGET_CONTAINER", "serving")
WINDOW_S = float(os.environ.get("WINDOW_S", "60"))
INTERVAL_S = 0.2
UPTIME_BAR = 95.0
MIN_RESTARTS = 5


class _Stop(Exception):
    pass


def _fail(reason) -> NoReturn:
    print("GREEN CHECK: FAIL (%s)" % reason)
    raise _Stop()


def docker(*args):
    r = subprocess.run(["docker", *args], capture_output=True, text=True, timeout=15)
    if r.returncode != 0:
        _fail("docker %s failed: %s" % (" ".join(args), r.stderr.strip()[:200]))
    return r.stdout.strip()


def restart_count():
    return int(docker("inspect", "--format", "{{.RestartCount}}", TARGET))


def chaos_is_running():
    names = docker("ps", "--format", "{{.Names}}").splitlines()
    return any("chaos" in n for n in names)


def poll_once():
    try:
        with urllib.request.urlopen(BASE + "/health", timeout=1.0) as r:
            return r.status == 200
    except Exception:
        return False


def main():
    docker("inspect", "--format", "{{.State.Status}}", TARGET)
    if not chaos_is_running():
        _fail("no running container with 'chaos' in its name; the drill must be "
              "measured while chaos is on")

    r0 = restart_count()
    ok = total = 0
    t_end = time.monotonic() + WINDOW_S
    next_tick = time.monotonic()
    while time.monotonic() < t_end:
        total += 1
        ok += poll_once()
        next_tick += INTERVAL_S
        time.sleep(max(0.0, next_tick - time.monotonic()))
    r1 = restart_count()

    uptime = 100.0 * ok / total if total else 0.0
    restarts = r1 - r0
    print("window %.0fs: %d/%d ok (%.1f%%), %d restarts observed"
          % (WINDOW_S, ok, total, uptime, restarts))

    if total < 50:
        _fail("only %d polls landed; something is wrong with the loop itself" % total)
    if restarts < MIN_RESTARTS:
        _fail("only %d restarts in the window (need >= %d); chaos is not "
              "actually killing the service at drill cadence" % (restarts, MIN_RESTARTS))
    if uptime < UPTIME_BAR:
        _fail("uptime %.1f%% under chaos, target %.0f%%; the failure-modes "
              "section starts with service startup time" % (uptime, UPTIME_BAR))

    print("GREEN CHECK: PASS")


if __name__ == "__main__":
    try:
        main()
    except _Stop:
        raise SystemExit(1)
