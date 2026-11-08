# NCO Hybrid Search Dataset

## Metadata

| Field | Value |
|---|---|
| Name | NCO Hybrid Search Dataset |
| Version | 1.0 |
| Description | Small evaluation dataset for NCO occupational role retrieval |

This dataset is used to evaluate retrieval quality for NCO occupational roles
with the project's hybrid search system, combining keyword and semantic
matching.

## File

- [`hybrid_search_eval.json`](./hybrid_search_eval.json) - Evaluation metadata,
  search queries, and expected role results.

## Dataset Structure

The JSON file contains:

- `metadata` - Dataset name, version, description, and relevance scale.
- `queries` - Evaluation cases. Each query includes:
  - `query_id` - Unique identifier for the evaluation case.
  - `query` - User search text.
  - `category` - Query type, such as `exact_title` or `partial_title`.
  - `expected_results` - Expected role matches, each identified by
    `role_number` and assigned a relevance score.

Example:

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

## Relevance Scale

| Score | Meaning |
|---:|---|
| 0 | Not relevant |
| 1 | Somewhat relevant |
| 2 | Highly relevant |
| 3 | Exact or ideal match |

Higher scores indicate stronger matches. The expected results can be compared
with the roles returned by the search system to measure ranking and retrieval
quality.