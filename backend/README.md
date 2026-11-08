# NCO Semantic and Hybrid Search Backend

## Tech Stack

- Web Framework: FastAPI
- ASGI Server: Uvicorn
- Vector Database: Qdrant with Reciprocal Rank Fusion (RRF) hybrid search
- Dense Embeddings: FastEmbed `BAAI/bge-small-en-v1.5` (ONNX runtime optimized)
- Sparse Embeddings: FastEmbed `Qdrant/bm25` (native BM25 token statistics)
- Relational Store: SQLite
- Testing: Pytest, HTTPX

## Environment Configuration

Configuration is managed via environment variables or a `.env` file:

- `PORT`: Server port (default: `8000`).
- `HOST`: Server host (default: `0.0.0.0`).
- `DEBUG`: Boolean flag for debug mode (default: `false`).
- `SQLITE_DB_PATH`: Path to SQLite database file (default: `backend/db/roles.db`).
- `QDRANT_PATH`: Path to local Qdrant directory (default: `backend/db/qdrant_storage`).
- `QDRANT_URL`: Optional remote Qdrant endpoint for Qdrant Cloud.
- `QDRANT_API_KEY`: Optional API key for remote Qdrant.
- `COLLECTION_NAME`: Qdrant collection name (default: `nco_roles`).
- `EMBEDDING_MODEL_NAME`: FastEmbed dense model name (default: `BAAI/bge-small-en-v1.5`).
- `SPARSE_MODEL_NAME`: FastEmbed sparse model name (default: `Qdrant/bm25`).

## Running Locally

1. Install dependencies:
```bash
uv sync
```

2. Start the API:
```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

3. Ingest data:
```bash
uv run python -m app.cli.ingest --json-path data/json/formatted.json
```

## Running Tests

Run the test suite with coverage:
```bash
uv run pytest tests -v
```

Install `uv` from [astral.sh/uv](https://docs.astral.sh/uv/) and run commands
from the `backend/` directory. Use `uv sync --group dev` to install test and
benchmark tooling.


### Storage Options
1. Embedded Mode:
Include `backend/db/roles.db` and `backend/db/qdrant_storage` inside the Docker image for self-contained deployment.

2. Cloud Managed Mode:
Use Qdrant Cloud by setting `QDRANT_URL` and `QDRANT_API_KEY`.
