from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import quote


if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from quality.eval import evaluate, save_reports, validate_dataset
from utils.utils import dataset_digest, git_revision, load_json, write_json


def _search(
    base_url: str,
    query: str,
    top_k: int,
    timeout: float,
) -> list[dict[str, Any]]:
    payload = json.dumps(
        {
            "query": query,
            "top_k": top_k,
            "offset": 0,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/search",
        data=payload,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response_data = json.load(response)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Search request failed for query {query!r}: {error}") from error

    results = response_data.get("results") if isinstance(response_data, dict) else None
    if not isinstance(results, list):
        raise TypeError(f"Search response for query {query!r} has no results list.")

    run_results = []
    for result in results:
        if not isinstance(result, dict):
            raise TypeError(f"Search response for query {query!r} contains an invalid result.")
        role_number = result.get("role_number")
        role_title = result.get("role_title")
        score = result.get("combined_score", result.get("score"))
        if not isinstance(role_number, str) or not role_number:
            raise ValueError(f"Search response for query {query!r} has an invalid role number.")
        if not isinstance(role_title, str) or not role_title:
            raise ValueError(f"Search response for query {query!r} has an invalid role title.")
        if isinstance(score, bool) or not isinstance(score, (int, float)):
            raise TypeError(f"Search response for query {query!r} has an invalid score.")
        run_results.append(
            {"role_number": role_number, "role_title": role_title, "score": float(score)}
        )
    return run_results


def _get_role_title(base_url: str, role_number: str, timeout: float) -> str:
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/roles/{quote(role_number, safe='')}",
        headers={"Accept": "application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            role = json.load(response)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Role lookup failed for {role_number!r}: {error}") from error

    title = role.get("title") if isinstance(role, dict) else None
    if not isinstance(title, str) or not title:
        raise TypeError(f"Role lookup for {role_number!r} has an invalid title.")
    return title


def _check_api_health(base_url: str, timeout: float) -> None:
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/health",
        headers={"Accept": "application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            health = json.load(response)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Health check failed: {error}") from error

    if not isinstance(health, dict):
        raise TypeError("Health check returned an invalid JSON object.")

    if health.get("vector_count", 0) == 0:
        raise RuntimeError(
            "Search index is empty: /health reports vector_count=0. "
            "Ingest the NCO data into the same Qdrant instance used by the server, "
            "then rerun the pipeline."
        )
    if health.get("qdrant_status") is not True:
        raise RuntimeError("Search index is unavailable: /health reports qdrant_status=false.")


def collect_run(
    dataset: dict[str, Any],
    base_url: str,
    top_k: int,
    timeout: float,
) -> list[dict[str, Any]]:
    """Collect one deterministic run contract from the configured search API."""
    queries = dataset["queries"]
    return [
        {
            "query_id": query["query_id"],
            "results": _search(
                base_url,
                query.get("query", ""),
                top_k,
                timeout,
            ),
        }
        for query in queries
    ]

def write_difference_json(
    query_map:dict,
    run_map:dict,
    output_dir: Path,
    base_url: str,
    timeout: float,
    run_titles: dict
    ) -> None:
    difference_json = {}
    for query_id, query_info in query_map.items():
        expected_roles = {
            role_number
            for role_number, relevance in query_info["judgments"].items()
            if relevance > 0
        }
        retrieved_results = run_map.get(query_id, [])
        retrieved_roles = {role_number for role_number, _ in retrieved_results}
        missing_roles = [
            {
                "role_number": role_number,
                "role_title": _get_role_title(base_url, role_number, timeout),
                "relevance": relevance,
            }
            for role_number, relevance in query_info["judgments"].items()
            if relevance > 0 and role_number not in retrieved_roles
        ]
        unexpected_results = [
            {
                "role_number": role_number,
                "role_title": run_titles[query_id][role_number],
                "score": score,
            }
            for role_number, score in retrieved_results
            if role_number not in expected_roles
        ]
        if missing_roles or unexpected_results:
            difference_json[query_id] = {
                "query": query_info["query"],
                "query_map": missing_roles,
                "run": unexpected_results,
            }

    write_json(output_dir / "differences.json", difference_json)


def run_pipeline(
    dataset_path: Path,
    output_dir: Path,
    base_url: str,
    top_k: int,
    timeout: float,
) -> None:
    dataset = load_json(dataset_path)
    query_map = validate_dataset(dataset)
    _check_api_health(base_url, timeout)
    run_data = collect_run(
        dataset,
        base_url,
        top_k,
        timeout,
    )
    run_path = output_dir / "run.json"
    write_json(run_path, run_data)

    from quality.eval import validate_run

    run_map = validate_run(run_data, query_map)
    run_titles = {
        entry["query_id"]: {
            result["role_number"]: result["role_title"] for result in entry["results"]
        }
        for entry in run_data
    }
    write_difference_json(query_map,run_map,output_dir,base_url,timeout,run_titles)
    summary, per_query = evaluate(query_map, run_map)
    save_reports(output_dir, summary, per_query)

    write_json(
        output_dir / "run_manifest.json",
        {
            "dataset": str(dataset_path),
            "dataset_sha256": dataset_digest(dataset_path),
            "git_revision": git_revision(),
            "search": {
                "base_url": base_url.rstrip("/"),
                "endpoint": "/search",
                "top_k": top_k,
                "timeout_seconds": timeout,
            },
            "artifacts": {
                "run": "run.json",
                "differences": "differences.json",
                "metrics": "metrics.json",
                "query_analysis": "query_analysis.csv",
            },
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect a search run and evaluate it reproducibly.")
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--base-url", required=True, help="Base URL of the running search API.")
    parser.add_argument("--output", type=Path, default=Path("reports/latest"))
    parser.add_argument("--top-k", type=int, default=100)
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()

    if not 1 <= args.top_k <= 100:
        parser.error("--top-k must be between 1 and 100")
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    try:
        run_pipeline(
            args.dataset,
            args.output,
            args.base_url,
            args.top_k,
            args.timeout,
        )
    except (OSError, TypeError, ValueError, RuntimeError, KeyError) as error:
        print("Exception",error)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
