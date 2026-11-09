# Quality Evaluation of Hybrid Search API

This folder provides a reproducible two-stage quality pipeline:

1. `pipeline.py` queries a running search API for every dataset query and
   writes a validated retrieval run.
2. `eval.py` scores that run against manually assigned relevance judgments.

The pipeline records the dataset SHA-256, Git revision, API settings, and
artifact names in `run_manifest.json`. Reports are deterministic for the same
dataset and run.

## End-to-end evaluation

Run commands from `backend/benchmark` so the local benchmark packages resolve.
Start the API and ensure its database/vector index are available, then run:

```bash
python quality/pipeline.py \
  --dataset data/hybrid_search_eval.json \
  --base-url http://127.0.0.1:8000 \
  --output quality/reports/latest \
  --top-k 100
```

The command writes `run.json`, `differences.json`, `metrics.json`,
`query_analysis.csv`, and `run_manifest.json` under the output directory.
`differences.json` lists mismatches in both directions, grouped by query:
`query_map` contains positively judged roles missing from the run, while `run`
contains retrieved roles that are not positively judged. Existing files with
the same names are replaced atomically.

Use a unique output directory for historical comparisons, for example
`quality/reports/2026-11-08-baseline`. Do not commit generated reports unless
they are intended as a benchmark baseline.

## Re-evaluating an existing run

Collection and evaluation are intentionally separable. To evaluate an
existing run without contacting the API:

```bash
python quality/eval.py \
  --dataset data/hybrid_search_eval.json \
  --run quality/reports/latest/run.json \
  --output quality/reports/latest
```

`eval.py` arguments:

| Argument | Required | Description |
|---|---:|---|
| `--dataset` | Yes | Dataset JSON containing the evaluation queries. |
| `--run` | Yes | JSON array containing retrieval results. |
| `--output` | No | Report directory. Defaults to `reports`. It is created if needed. |

`pipeline.py` arguments:

| Argument | Default | Description |
|---|---:|---|
| `--dataset` | — | Relevance-judgment dataset. |
| `--base-url` | — | Running API base URL; requests are sent to `POST /search`. |
| `--output` | `reports/latest` | Directory for all artifacts. |
| `--top-k` | `100` | Number of API results requested per query. |
| `--timeout` | `30` | Per-query HTTP timeout in seconds. |

The pipeline fails instead of producing a partial success-shaped report when a
request, response, or run entry is invalid. Before collecting queries it calls
`GET /health` and refuses to continue when `vector_count` is zero or
`qdrant_status` is false. This prevents an unindexed server from producing
misleading all-zero quality reports.

If the health check reports `vector_count: 0`, ingest the source data using the
same environment and storage configuration as the running server:

```bash
cd backend
python -m app.cli.ingest --json-path path/to/formatted.json
```

Restart the API if its Qdrant client was initialized before ingestion, verify
`GET http://127.0.0.1:8000/health` reports a positive `vector_count`, and then
rerun the pipeline.

## Metrics

Metrics are calculated for every query and then macro-averaged; queries are
weighted equally regardless of how many judgments they contain.

| Metric | Definition |
|---|---|
| `precision@5` | Relevant retrieved roles in the first five results divided by 5. Relevance `>= 1` is relevant. |
| `recall@5` | Relevant retrieved roles in the first five results divided by all relevant judged roles. |
| `mrr@10` | Reciprocal rank of the first relevant role in the first ten results, or `0` if none is found. |
| `ndcg@5` | Graded NDCG over the first five results using gain `2^relevance - 1`. Unjudged roles have relevance `0`. |

If fewer than five results are returned, precision still uses a denominator of
5. Results are ranked by descending retrieval score; ties are broken by
`role_number` in ascending order.

## Dataset Structure

The dataset is a JSON object with a non-empty `queries` array. Each query must
contain:

```json
{
  "query_id": "Q001",
  "query": "Web Developer",
  "category": "exact_title",
  "expected_results": [
    {
      "role_number": "2513.0101",
      "relevance": 3
    }
  ]
}
```

Validation rules:

- `query_id` and each `role_number` must be non-empty strings and unique in
  their respective lists.
- `category` must be a non-empty string.
- `expected_results` must contain at least one judgment.
- `relevance` must be an integer from `0` to `3`; at least one judgment must be
  greater than `0`.
- The optional `query` field is retained for dataset context but is not used
  directly by the evaluator.

The relevance scale is:

| Score | Meaning |
|---:|---|
| 0 | Not relevant |
| 1 | Somewhat relevant |
| 2 | Highly relevant |
| 3 | Exact or ideal match |

## Run Structure

The run is a JSON array with at most one entry per dataset query:

```json
[
  {
    "query_id": "Q001",
    "results": [
      {
        "role_number": "2513.0101",
        "score": 0.98
      },
      {
        "role_number": "2513.0199",
        "score": 0.42
      }
    ]
  }
]
```

Each result requires a unique non-empty `role_number` and a finite numeric
`score` (boolean values are not accepted as scores). The evaluator sorts results
itself, so the input order does not need to be ranked. Run query IDs must exist
in the dataset, and duplicate query entries are rejected. Dataset queries
missing from the run are treated as having no retrieved results; extra or
unknown query IDs are rejected.

## Reports

The output directory contains:

### `metrics.json`

```json
{
  "overall": {
    "precision@5": 0.2,
    "recall@5": 1.0,
    "mrr@10": 1.0,
    "ndcg@5": 1.0
  },
  "by_category": {
    "exact_title": {
      "query_count": 1,
      "metrics": {
        "precision@5": 0.2,
        "recall@5": 1.0,
        "mrr@10": 1.0,
        "ndcg@5": 1.0
      }
    }
  },
  "query_count": 1
}
```

`by_category` contains the same macro-averaged metrics plus the number of
queries in each category.

### `query_analysis.csv`

The CSV contains one row per dataset query with these columns:

```text
query_id,category,precision@5,recall@5,mrr@10,ndcg@5
```

The script also prints the output paths and overall metrics to standard output.
