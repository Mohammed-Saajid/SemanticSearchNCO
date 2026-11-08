from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


def _git_revision() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(__file__).resolve().parents[3],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture a low-overhead py-spy profile from a running API process.")
    parser.add_argument("--pid", type=int, required=True, help="PID of the API process.")
    parser.add_argument("--duration", type=int, default=30, help="Capture duration in seconds.")
    parser.add_argument(
        "--rate",
        type=int,
        default=50,
        help="Sampling frequency in Hz.",
    )
    parser.add_argument("--output", type=Path, default=Path("reports/profile.svg"))
    parser.add_argument(
        "--format",
        choices=("flamegraph", "raw", "speedscope"),
        default="flamegraph",
        help="py-spy output format.",
    )
    args = parser.parse_args()

    if args.pid <= 0:
        parser.error("--pid must be positive")
    if args.duration <= 0:
        parser.error("--duration must be positive")
    if args.rate <= 0:
        parser.error("--rate must be positive")

    py_spy = shutil.which("py-spy")
    if py_spy is None:
        raise SystemExit("py-spy is required. Install benchmark dependencies with: uv sync --group dev")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        py_spy,
        "record",
        "--pid",
        str(args.pid),
        "--duration",
        str(args.duration),
        "--rate",
        str(args.rate),
        "--format",
        args.format,
        "--output",
        str(args.output),
        "--subprocesses",
    ]
    subprocess.run(command, check=True)

    manifest = {
        "captured_at": datetime.now(UTC).isoformat(),
        "git_revision": _git_revision(),
        "pid": args.pid,
        "duration_seconds": args.duration,
        "sample_rate_hz": args.rate,
        "format": args.format,
        "output": str(args.output),
        "python": sys.version,
        "platform": platform.platform(),
        "command": command,
        "environment": {
            "BENCHMARK_BASE_URL": os.environ.get("BENCHMARK_BASE_URL"),
            "BENCHMARK_DATASET": os.environ.get("BENCHMARK_DATASET"),
        },
    }
    manifest_path = args.output.with_suffix(f"{args.output.suffix}.manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
