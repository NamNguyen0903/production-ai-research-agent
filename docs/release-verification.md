# v1.0.0 Release Verification

Verification performed on 2026-09-17 against the current working tree.

| Check | Result | Evidence |
|---|---|---|
| `uv run ruff check .` | Pass | `All checks passed!` |
| `uv run pytest -q` | Pass | 34 passed, 2 infrastructure-only tests skipped |
| Infrastructure tests | Pass | 2 passed against local PostgreSQL |
| Docker build | Pass | `production-ai-research-agent:test` built successfully |
| Clean Compose restart | Pass | API, PostgreSQL, and Redis healthy |
| `GET /health` | Pass | `{"status":"ok"}` |
| `GET /ready` | Pass | PostgreSQL and Redis reported `ok` |
| `POST /v1/research` | Pass | Completed, verified response with metrics and latency |
| `GET /v1/research/{run_id}` | Pass | Completed metadata row returned |
| Run metadata | Pass | PostgreSQL row contained latency, calls, iterations, sources, score |
| Redis cache | Pass | 3 hashed web-search cache keys after the run |
| LangGraph checkpoint | Pass | 7 checkpoint rows for the run's `thread_id` |
| Langfuse trace | Pass | Matching `research-agent` trace retrieved through the Langfuse API |

## End-to-End Run

Run ID: `0a92e4e7-dd08-4d58-a8b1-26354f2b3e49`

- Status: `completed`
- Plan steps/tool calls: 3
- Sources: 12
- Iterations: 1
- Latency: 11,468 ms
- Tool errors: 0
- Citation validity: true
- Verification passed: true
- Coverage: 1.0
- PostgreSQL metadata row: present
- Redis cache entries created: 3
- LangGraph checkpoint rows: 7
- Langfuse trace: present with matching run ID

## Release Status

All application, infrastructure, end-to-end API, persistence, caching,
checkpointing, and optional tracing checks passed. No secret values were printed or
committed.

The test suite also emits one warning from Starlette's installed `TestClient` dependency using a deprecated AnyIO alias. It is outside the application code and does not fail the suite.

## Git Commands

Review before committing:

```bash
git status
git add .
git commit -m "docs: finalize evaluation and portfolio documentation"
git tag v1.0.0
```

The GitHub release commands are executed after this report is committed.
