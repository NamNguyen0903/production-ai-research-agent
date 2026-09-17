# Production-Readiness Review

Review scope: application code, configuration, API lifecycle, LangGraph state/routing, LLM adapters, Tavily integration, evidence and verification logic, PostgreSQL, checkpoints, Redis, Langfuse, Docker, CI, tests, evaluation harness, and release files.

## Blockers

No release blockers found.

No committed secret was found by the repository scan. `.env` is ignored, `.env.example` contains blank credential values, Docker excludes `.env*`, and API keys are represented with Pydantic `SecretStr`.

## Important

### Addressed for v1.0.0

1. **Optional Redis caching could abort research.** Cache reads occurred before Tavily's tool-error boundary, so Redis connection or serialization errors could fail the graph. Cache reads now degrade to misses, invalid entries are ignored, failed writes are skipped, and health pings return `false` on Redis errors. Tests cover unavailable Redis and malformed JSON.
2. **Readiness dependency exceptions could become HTTP 500.** PostgreSQL or Redis ping exceptions are now converted into the existing 503 not-ready response.
3. **Local Langfuse settings were incomplete.** Pydantic did not declare the public key, secret key, base URL, or tracing environment. Docker's `env_file` happened to export them, but local settings loading did not configure the SDK explicitly. The app now validates credentials when tracing is enabled, constructs the current Langfuse client explicitly, passes its public key to the callback handler, and shuts the client down during lifespan cleanup.
4. **Release metadata still said 0.1.0.** `pyproject.toml`, `uv.lock`, and FastAPI metadata now report `1.0.0`, and the placeholder package description was replaced.
5. **Ruff failed on the evaluation runner.** The import block was normalized.
6. **Generated reports were not governed.** Timestamped evaluation history is now ignored, while `evals/reports/latest.json` remains the committed canonical benchmark and `.gitkeep` preserves the directory.

### Known important quality gap

The evaluation contains two answers with sufficient evidence and `coverage_score=1.0` but no valid citations. The graph correctly reports verification failure, and the absence of `missing_queries` correctly prevents a redundant search retry. However, there is no citation-only repair/resynthesis branch. This is documented as the next quality improvement rather than added during a v1 finalization pass.

## Optional

- Add dedicated Langfuse spans for Tavily requests, cache hits/misses, and per-stage latency. Current callbacks trace graph/LLM activity and root run metrics, but custom HTTP calls are not explicit child spans.
- Add an authenticated background-job API before exposing the service publicly. The current synchronous endpoint has no auth, rate limiting, or job queue.
- Add independent source-authority scoring and primary-source rules. Current ranking uses Tavily relevance scores.
- Add structured application logging with run IDs and redaction policy. The current code has minimal warning logging for cache degradation.
- Add tests for LLM malformed-output failure, partial Tavily failure across multiple concurrent steps, readiness ping exceptions, and Langfuse-enabled startup.
- Add a public resume endpoint only if product requirements need it. Checkpoints and `thread_id` exist, but the current API starts new runs and exposes metadata only.

## Area-by-Area Notes

### Security and configuration

- No tracked `.env` or detected key literals.
- Secrets are not returned by the API or written to prompts.
- Development defaults use `LLM_PROVIDER=mock`, so CI does not require external API credentials.
- The Docker Compose PostgreSQL password is a local-development credential and must not be reused for deployment.
- Public deployment still requires authentication, authorization, rate limiting, TLS termination, and a secret manager.

### FastAPI and lifecycle

- Infrastructure initialization and cleanup use FastAPI lifespan.
- PostgreSQL pool, Redis client, Tavily HTTP client, checkpointer context, and Langfuse client have cleanup paths.
- Request fields enforce query length and an iteration range of one to five.
- `/health` is a liveness probe; `/ready` checks PostgreSQL and Redis.
- Unexpected run exceptions propagate as HTTP 500 after the metadata row is marked failed. There is no custom sanitized API error envelope.

### LangGraph and execution budgets

- `ResearchState` includes the plan, evidence, answer, verification, retry queries, errors, iteration count, tool calls, and both budgets.
- Verification routes to retry only when it fails, iteration and tool budgets remain, and targeted queries exist.
- `thread_id` equals the generated run ID.
- PostgreSQL checkpoint setup occurs at startup and its context is closed at shutdown.
- `GRAPH_RECURSION_LIMIT` is passed on every invocation.

### LLM and tools

- Planner, synthesizer, and verifier use Pydantic structured outputs; provider temperature is zero.
- Google, OpenAI, and mock modes are supported through a factory and dependency-injected nodes.
- Malformed structured output fails the run rather than silently accepting invalid state.
- Tavily uses an async client and configurable timeout; searches are concurrent.
- Recognized Tavily/HTTP/validation failures are abstracted and contained per step.

### Evidence and verification

- URLs are normalized, evidence is deduplicated, provider relevance scores determine ranking, and source IDs are reassigned after processing.
- Citation membership is deterministic.
- Verifier-supplied evidence IDs are filtered against available evidence.
- Coverage is calculated in Python from per-claim decisions.
- Retry queries are deduplicated and capped.

### Persistence, cache, and tracing

- The database repository uses a bounded async pool and explicit commits.
- Running, completed, and failed statuses are persisted.
- Metadata and framework checkpoints have separate schemas and responsibilities.
- Redis cache keys contain normalized query text and `max_results`, not run-specific step IDs; cached evidence is remapped to the active step.
- Langfuse is optional and uses the installed v4 client API. Shutdown flushes buffered telemetry.

### Docker and CI

- The Docker build uses Python 3.12, a pinned uv image, the lockfile, and a non-root UID.
- `.dockerignore` excludes `.git`, `.venv`, local environments, tests, and generated reports.
- Compose uses internal service hostnames and health-based dependencies.
- CI uses pinned action revisions, starts PostgreSQL and Redis, runs Ruff, the full test suite, explicit infrastructure tests, and a Docker build in mock mode.

### Tests

- Unit tests cover the main deterministic logic and service boundaries.
- API and graph integration tests run without provider keys.
- Opt-in infrastructure tests exercise `research_runs` and LangGraph checkpoints against PostgreSQL.
- There is no load, security, adversarial prompt-injection, or live-provider test in CI.
