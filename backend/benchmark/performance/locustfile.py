from __future__ import annotations

import hashlib
import json
import os
from itertools import cycle
from pathlib import Path
from typing import Any

from locust import HttpUser, LoadTestShape, between, task


ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = Path(
    os.environ.get(
        "BENCHMARK_DATASET",
        str(ROOT / "benchmark" / "data" / "hybrid_search_eval.json"),
    )
)


def _queries() -> list[dict[str, Any]]:
    with DATASET_PATH.open(encoding="utf-8") as file:
        dataset = json.load(file)
    queries = dataset.get("queries")
    if not isinstance(queries, list) or not queries:
        raise ValueError(f"{DATASET_PATH} must contain a non-empty queries list")
    if any(not isinstance(item.get("query"), str) or not item["query"] for item in queries):
        raise ValueError(f"{DATASET_PATH} contains a query without search text")
    return queries


QUERIES = _queries()
QUERY_SET_SHA256 = hashlib.sha256(json.dumps(QUERIES, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class SearchUser(HttpUser):
    """Issue a deterministic cyclic workload against POST /search."""

    wait_time = between(0.5, 1.5)
    host = os.environ.get("BENCHMARK_BASE_URL", "http://127.0.0.1:8000")

    def on_start(self) -> None:
        self._query_cycle = cycle(QUERIES)

    @task
    def search(self) -> None:
        query = next(self._query_cycle)
        self.client.post(
            "/search",
            name=f"/search [{query['query_id']}]",
            json={"query": query["query"], "top_k": 10, "offset": 0},
        )


class StagedLoadShape(LoadTestShape):
    """Ramp through fixed stages so benchmark runs are comparable."""

    stages = (
        {"duration": 20, "users": 2, "spawn_rate": 1},
        {"duration": 50, "users": 6, "spawn_rate": 2},
        {"duration": 80, "users": 10, "spawn_rate": 2},
        {"duration": 90, "users": 0, "spawn_rate": 2},
    )

    def tick(self) -> tuple[int, float] | None:
        run_time = self.get_run_time()
        for stage in self.stages:
            if run_time < stage["duration"]:
                return stage["users"], stage["spawn_rate"]
        return None
