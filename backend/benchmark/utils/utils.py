import json
from typing import Any
from pathlib import Path
import subprocess
import hashlib

def load_json(path: Path) -> Any:
    """Load JSON data from a file."""
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)
    
def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(f"{path.suffix}.tmp")
    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump(value, file, indent=4, sort_keys=True)
        file.write("\n")
    temporary_path.replace(path)


def dataset_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_revision() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None