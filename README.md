# SemanticSearchNCO

Hybrid semantic search for the Indian **National Classification of
Occupations (NCO) 2015** dataset. The backend combines dense vector retrieval,
sparse BM25 retrieval, and Qdrant Reciprocal Rank Fusion (RRF) to return
ranked occupational roles through a FastAPI service.

## Features

- Hybrid dense and sparse retrieval
- FastEmbed embeddings:
  - Dense: `BAAI/bge-small-en-v1.5`
  - Sparse: `Qdrant/bm25`
- Qdrant vector storage with local or cloud deployment options
- SQLite role metadata storage
- React and Vite frontend
- Reproducible retrieval-quality evaluation
- Ruff, Bandit, Mypy, and pre-commit quality checks

The API currently uses synchronous service and repository operations. This is intentional

## Requirements

- Python 3.14 or newer
- [`uv`](https://docs.astral.sh/uv/)
- Node.js and npm
- Docker, optional

The backend Python version is pinned in
[`backend/.python-version`](./backend/.python-version), and dependency
versions are locked in [`backend/uv.lock`](./backend/uv.lock).

## Quick start

### Backend

```bash
cd backend
uv sync
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The API is available at:

- API: <http://127.0.0.1:8000>
- OpenAPI documentation: <http://127.0.0.1:8000/docs>
- Health check: <http://127.0.0.1:8000/health>

### Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

The development frontend is available at <http://localhost:5173>.

## Configuration

Backend settings can be supplied through environment variables or
`backend/.env`:

| Variable | Default | Description |
|---|---|---|
| `HOST` | `0.0.0.0` | API bind address |
| `PORT` | `8000` | API port |
| `DEBUG` | `false` | Enables debug behavior |
| `SQLITE_DB_PATH` | `db/roles.db` | SQLite metadata database |
| `QDRANT_PATH` | `db/qdrant_storage` | Local Qdrant storage |
| `QDRANT_URL` | unset | Optional Qdrant Cloud endpoint |
| `QDRANT_API_KEY` | unset | Optional Qdrant API key |
| `COLLECTION_NAME` | `nco_roles` | Qdrant collection |
| `EMBEDDING_MODEL_NAME` | `BAAI/bge-small-en-v1.5` | Dense model |
| `SPARSE_MODEL_NAME` | `Qdrant/bm25` | Sparse model |

Set `QDRANT_URL` and `QDRANT_API_KEY` to use a remote Qdrant instance.
Otherwise, the application uses the local database paths under `backend/db`.

## API

### Search

```bash
curl -X POST http://127.0.0.1:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query":"software architect","top_k":10,"offset":0}'
```

### Role description

```bash
curl "http://127.0.0.1:8000/getroledescription?role_number=1001.0100"
```

### Role details

```bash
curl http://127.0.0.1:8000/roles/1001.0100
```

Interactive API documentation is available at `/docs`, with the OpenAPI
schema at `/openapi.json`.

## Data ingestion

To index a compatible formatted JSON dataset into SQLite and Qdrant:

```bash
cd backend
uv run python -m app.cli.ingest \
  --json-path path/to/formatted.json \
  --batch-size 64
```

The ingestion command uses the same environment configuration as the running
API. Restart the API after ingestion when using local Qdrant storage.

## Development and validation

Install development tools:

```bash
cd backend
uv sync --group dev
```

Run the test suite:

```bash
uv run pytest tests -q
```

Run static checks:

```bash
uv run ruff check app tests benchmark
uv run ruff format --check app tests benchmark
uv run bandit --recursive app
uv run mypy app
```

Install and run pre-commit from the repository root:

```bash
uv run --project backend pre-commit install
uv run --project backend pre-commit run --all-files
```

## Performance and quality benchmarks

The quality pipeline evaluates retrieval relevance using the dataset in
[`backend/benchmark/data`](./backend/benchmark/data):

```bash
cd backend/benchmark
uv run python quality/pipeline.py \
  --dataset data/hybrid_search_eval.json \
  --base-url http://127.0.0.1:8000 \
  --output quality/reports/latest
```

[performance benchmark guide](./backend/benchmark/performance/README.md).
The default workload uses eight users, a gentle ramp-up, and a 90-second run.

## Docker

Build and run the backend from the `backend/` directory:

```bash
cd backend
docker build -t semantic-search-api .
docker run --rm -p 8000:8000 semantic-search-api
```

The image uses Python 3.13, installs locked production dependencies with
`uv`, runs as a non-root user, and includes a `/health` container
health check. For persistent local data, mount the database directory:

```bash
docker run --rm -p 8000:8000 \
  -v "$PWD/db:/app/db" \
  semantic-search-api
```

## Data source

The project is based on the NCO 2015 occupational classification published by
the Government of India. Ensure that any redistributed source data complies
with its applicable license and attribution requirements.
