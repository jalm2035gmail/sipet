#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from collections import deque
from pathlib import Path


def _write_snapshot(log_file: Path, lines: deque[str]) -> None:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = log_file.with_suffix(log_file.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as fh:
        fh.writelines(lines)
    os.replace(tmp_path, log_file)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a command and cap its log file to the last N lines.")
    parser.add_argument("--log-file", required=True)
    parser.add_argument("--max-lines", type=int, default=1000)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    command = list(args.command)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise SystemExit("Missing command to execute.")

    max_lines = max(1, int(args.max_lines or 1000))
    log_file = Path(args.log_file).resolve()
    history: deque[str] = deque(maxlen=max_lines)

    if log_file.exists():
        try:
            existing = log_file.read_text(encoding="utf-8", errors="ignore").splitlines(True)
            history.extend(existing[-max_lines:])
        except OSError:
            pass

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    assert process.stdout is not None
    last_flush = 0.0
    dirty = False
    flush_interval_seconds = 1.0
    flush_every_lines = 25
    pending_since_flush = 0

    try:
        for line in process.stdout:
            history.append(line)
            dirty = True
            pending_since_flush += 1
            sys.stdout.write(line)
            sys.stdout.flush()

            now = time.monotonic()
            if pending_since_flush >= flush_every_lines or now - last_flush >= flush_interval_seconds:
                _write_snapshot(log_file, history)
                dirty = False
                pending_since_flush = 0
                last_flush = now
    finally:
        return_code = process.wait()
        if dirty or not log_file.exists():
            _write_snapshot(log_file, history)

    return int(return_code)


if __name__ == "__main__":
    raise SystemExit(main())
