# API performance benchmark and profiling

This benchmark uses [Locust](https://locust.io/) for concurrent HTTP load and
[py-spy](https://github.com/benfred/py-spy) for low-overhead sampling profiles.
The workload is the versioned relevance dataset used by the quality pipeline,
so performance measurements and retrieval quality are evaluated against the
same search cases.

## Reproducible load test

Run from `backend/` with the API already started and its index populated:

```bash
uv run python -m benchmark.performance.run \
  --users 8 \
  --spawn-rate 2 \
  --run-time 90s \
  --output benchmark/reports/load
```

The command writes Locust CSV and HTML outputs plus
`benchmark/reports/load.manifest.json`. The manifest records the request
parameters, dataset hash, Git revision, Python/platform details, command, and
exit status. The CSV and HTML outputs contain request count, failures,
throughput, and latency percentiles. Use a unique output prefix for historical
comparisons.
The workload is deterministic in query selection; concurrency means individual
request ordering is intentionally not deterministic.

The staged profile is also available:

```bash
uv run locust -f benchmark/performance/locustfile.py \
  --headless --shape StagedLoadShape \
  --csv benchmark/reports/staged --only-summary
```

Set `BENCHMARK_BASE_URL` to target another API host and
`BENCHMARK_DATASET` to run a compatible JSON dataset. The default dataset is
`benchmark/data/hybrid_search_eval.json`.

## CPU profiling

Start the API normally, find its PID, and capture a flamegraph while the load
test is running:

```bash
uv run python -m benchmark.performance.profile \
  --pid "$(pgrep -f 'uvicorn app.main:app' | head -n 1)" \
  --duration 30 \
  --rate 50 \
  --output benchmark/performance/reports/search.svg
```

The wrapper records the exact command, Git revision, Python/platform details,
and benchmark environment in a sidecar manifest. It fails explicitly when
`py-spy` is unavailable or the target process cannot be profiled.

## Comparing runs

Keep the following constant when comparing revisions:

- Python version and dependency lockfile (`uv.lock`)
- API configuration and database/index snapshot
- Locust users, spawn rate, duration, and dataset
- Host CPU, memory, and whether the API is local or remote

Do not commit generated reports unless they are an intentional performance
baseline. The quality pipeline remains separate:
`benchmark/quality/pipeline.py` measures retrieval quality, while this folder
measures service performance.
