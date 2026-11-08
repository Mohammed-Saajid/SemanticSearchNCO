from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from benchmark.performance.locustfile import DATASET_PATH, QUERY_SET_SHA256

ROOT = Path(__file__).resolve().parents[3]


def _git_revision() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a reproducible Locust search benchmark and write its manifest."
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--users", type=int, default=8)
    parser.add_argument("--spawn-rate", type=float, default=2)
    parser.add_argument("--run-time", default="90s")
    parser.add_argument("--output", type=Path, default=Path("benchmark/reports/load"))
    args = parser.parse_args()

    if args.users <= 0:
        parser.error("--users must be positive")
    if args.spawn_rate <= 0:
        parser.error("--spawn-rate must be positive")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "locust",
        "-f",
        str(Path(__file__).with_name("locustfile.py")),
        "--headless",
        "--host",
        args.base_url,
        "--users",
        str(args.users),
        "--spawn-rate",
        str(args.spawn_rate),
        "--run-time",
        args.run_time,
        "--csv",
        str(args.output),
        "--html",
        f"{args.output}.html",
        "--only-summary",
    ]
    started_at = datetime.now(UTC)
    completed = subprocess.run(command, cwd=ROOT / "backend", check=False)
    manifest = {
        "started_at": started_at.isoformat(),
        "completed_at": datetime.now(UTC).isoformat(),
        "git_revision": _git_revision(),
        "python": sys.version,
        "platform": platform.platform(),
        "dataset": str(DATASET_PATH),
        "dataset_query_sha256": QUERY_SET_SHA256,
        "base_url": args.base_url.rstrip("/"),
        "users": args.users,
        "spawn_rate": args.spawn_rate,
        "run_time": args.run_time,
        "artifacts": {
            "csv_prefix": str(args.output),
            "html": f"{args.output}.html",
        },
        "command": command,
        "exit_code": completed.returncode,
    }
    manifest_path = args.output.with_suffix(f"{args.output.suffix}.manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Load manifest saved to: {manifest_path}")
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
