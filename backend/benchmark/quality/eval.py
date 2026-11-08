from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path


if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.utils import load_json


def validate_dataset(dataset: dict) -> dict:
    """Validate dataset structure and relevance judgments."""
    if not isinstance(dataset, dict):
        raise ValueError("dataset must be a JSON object.")

    queries = dataset.get("queries")

    if not isinstance(queries, list) or not queries:
        raise ValueError("dataset must contain a non-empty queries list.")

    query_map = {}

    for query in queries:
        query_id = query.get("query_id")
        category = query.get("category")
        expected = query.get("expected_results")

        if not query_id or not isinstance(query_id, str):
            raise ValueError("Every query must have a valid query_id.")

        if query_id in query_map:
            raise ValueError(f"Duplicate query_id: {query_id}")

        if not isinstance(category, str) or not category:
            raise ValueError(f"Missing category for query {query_id}")

        if not isinstance(expected, list) or not expected:
            raise ValueError(f"Query {query_id} must have at least one judgment.")

        judgments = {}

        for item in expected:
            role_number = item.get("role_number")
            relevance = item.get("relevance")

            if not isinstance(role_number, str) or not role_number:
                raise ValueError(f"Invalid role_number in query {query_id}")

            if role_number in judgments:
                raise ValueError(f"Duplicate judgment: {query_id}, {role_number}")

            if isinstance(relevance, bool) or not isinstance(relevance, int) or relevance not in range(4):
                raise ValueError(f"Relevance must be an integer from 0 to 3: {query_id}, {role_number}")

            judgments[role_number] = relevance

        if not any(score > 0 for score in judgments.values()):
            raise ValueError(f"Query {query_id} has no relevant documents.")

        query_map[query_id] = {
            "query": query.get("query", ""),
            "category": category,
            "judgments": judgments,
        }

    return query_map


def validate_run(run_data: list, query_map: dict) -> dict:
    """Validate retrieval results and organize them by query."""
    if not isinstance(run_data, list):
        raise ValueError("Run file must contain a JSON array.")

    run_map = {}

    for entry in run_data:
        query_id = entry.get("query_id")

        if query_id not in query_map:
            raise ValueError(f"Unknown query_id in run: {query_id}")

        if query_id in run_map:
            raise ValueError(f"Duplicate run entry: {query_id}")

        results = entry.get("results")

        if not isinstance(results, list):
            raise ValueError(f"Results must be a list for query {query_id}")

        seen_roles = set()
        parsed_results = []

        for result in results:
            role_number = result.get("role_number")
            score = result.get("score")

            if not isinstance(role_number, str) or not role_number:
                raise ValueError(f"Invalid role_number in run for {query_id}")

            if role_number in seen_roles:
                raise ValueError(f"Duplicate retrieved role: {query_id}, {role_number}")

            if isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score):
                raise ValueError(f"Invalid retrieval score: {query_id}, {role_number}")

            seen_roles.add(role_number)
            parsed_results.append((role_number, float(score)))

        # Higher retrieval scores must appear first.
        parsed_results.sort(key=lambda item: (-item[1], item[0]))
        run_map[query_id] = parsed_results

    # Queries missing from the run are treated as having no results.
    for query_id in query_map:
        run_map.setdefault(query_id, [])

    return run_map


def precision_at_k(ranked_docs: list, judgments: dict, k: int) -> float:
    """Calculate Precision@K using relevance >= 1."""
    if k <= 0:
        raise ValueError("K must be positive.")

    retrieved = ranked_docs[:k]

    relevant_count = sum(judgments.get(role_number, 0) >= 1 for role_number, _ in retrieved)

    return relevant_count / k


def recall_at_k(ranked_docs: list, judgments: dict, k: int) -> float:
    """Calculate Recall@K using relevance >= 1."""
    if k <= 0:
        raise ValueError("K must be positive.")

    total_relevant = sum(relevance >= 1 for relevance in judgments.values())

    if total_relevant == 0:
        return 0.0

    retrieved_relevant = sum(judgments.get(role_number, 0) >= 1 for role_number, _ in ranked_docs[:k])

    return retrieved_relevant / total_relevant


def reciprocal_rank(ranked_docs: list, judgments: dict, k: int) -> float:
    """Calculate Reciprocal Rank@K."""
    if k <= 0:
        raise ValueError("K must be positive.")

    for rank, (role_number, _) in enumerate(ranked_docs[:k], start=1):
        if judgments.get(role_number, 0) >= 1:
            return 1.0 / rank

    return 0.0


def ndcg_at_k(ranked_docs: list, judgments: dict, k: int) -> float:
    """
    Calculate graded NDCG@K.

    Uses exponential gain: 2^relevance - 1.
    Unjudged documents receive relevance zero.
    """
    if k <= 0:
        raise ValueError("K must be positive.")

    def gain(relevance: int) -> float:
        return (2**relevance) - 1

    dcg = sum(gain(judgments.get(role_number, 0)) / math.log2(rank + 1) for rank, (role_number, _) in enumerate(ranked_docs[:k], start=1))

    ideal_relevances = sorted(judgments.values(), reverse=True)[:k]

    idcg = sum(gain(relevance) / math.log2(rank + 1) for rank, relevance in enumerate(ideal_relevances, start=1))

    return dcg / idcg if idcg > 0 else 0.0


def evaluate_query(ranked_docs: list, judgments: dict) -> dict:
    """Calculate all evaluation metrics for a single query."""
    return {
        "precision@5": precision_at_k(ranked_docs, judgments, 5),
        "recall@5": recall_at_k(ranked_docs, judgments, 5),
        "mrr@10": reciprocal_rank(ranked_docs, judgments, 10),
        "ndcg@5": ndcg_at_k(ranked_docs, judgments, 5),
    }


def aggregate_metrics(query_metrics: dict) -> dict:
    """Calculate macro-average metrics across queries."""
    if not query_metrics:
        return {}

    metric_names = [
        "precision@5",
        "recall@5",
        "mrr@10",
        "ndcg@5",
    ]

    query_count = len(query_metrics)

    return {metric: sum(values[metric] for values in query_metrics.values()) / query_count for metric in metric_names}


def evaluate(
    query_map: dict,
    run_map: dict,
) -> tuple[dict, dict]:
    """Evaluate all queries and calculate category-level metrics."""
    per_query = {}
    category_metrics = defaultdict(dict)

    for query_id, query_info in query_map.items():
        metrics = evaluate_query(
            run_map[query_id],
            query_info["judgments"],
        )

        per_query[query_id] = {
            "category": query_info["category"],
            **metrics,
        }

        category_metrics[query_info["category"]][query_id] = metrics

    summary = {
        "overall": aggregate_metrics(per_query),
        "by_category": {
            category: {
                "query_count": len(metrics),
                "metrics": aggregate_metrics(metrics),
            }
            for category, metrics in category_metrics.items()
        },
        "query_count": len(per_query),
    }

    return summary, per_query


def save_reports(
    output_dir: Path,
    summary: dict,
    per_query: dict,
) -> None:
    """Save aggregate JSON and per-query CSV reports."""
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_path = output_dir / "metrics.json"

    with summary_path.open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=4)

    csv_path = output_dir / "query_analysis.csv"

    fieldnames = [
        "query_id",
        "category",
        "precision@5",
        "recall@5",
        "mrr@10",
        "ndcg@5",
    ]

    with csv_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for query_id, metrics in per_query.items():
            writer.writerow(
                {
                    "query_id": query_id,
                    **metrics,
                }
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate NCO information retrieval quality.")

    parser.add_argument(
        "--dataset",
        type=Path,
        required=True,
        help="Path to dataset.json",
    )

    parser.add_argument(
        "--run",
        type=Path,
        required=True,
        help="Path to retrieval run JSON",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports"),
        help="Directory for evaluation reports",
    )

    args = parser.parse_args()

    dataset = load_json(args.dataset)
    run_data = load_json(args.run)

    query_map = validate_dataset(dataset)
    run_map = validate_run(run_data, query_map)

    summary, per_query = evaluate(query_map, run_map)

    save_reports(args.output, summary, per_query)

    for _metric, _value in summary["overall"].items():
        pass


if __name__ == "__main__":
    main()
