# CV Project Entry

## Production AI Research Agent

**Stack:** Python 3.12, FastAPI, LangGraph, Gemini, Tavily, PostgreSQL, Redis, Langfuse, Pydantic, Pytest, Ruff, Docker Compose, GitHub Actions

- Built a typed LangGraph research workflow that converts user questions into structured plans, executes Tavily searches concurrently, normalizes/deduplicates/ranks evidence, and synthesizes answers grounded with stable `[src-x]` citations.
- Implemented reliability controls including deterministic citation-ID validation, LLM-based claim verification with backend-calculated coverage, targeted missing-evidence retries, tool/iteration/recursion budgets, PostgreSQL run metadata and checkpoints, Redis search caching, and optional Langfuse tracing.
- Created unit, integration, infrastructure, Docker, and GitHub Actions CI coverage plus a 30-query evaluation harness; the recorded run completed 30/30 queries with 93.33% research success, 93.33% citation validity, 100% tool success, 13.25 s p50 latency, and 48.91 s p95 latency.

The metrics above come from `evals/reports/latest.json` and describe one recorded evaluation run, not production traffic or load-test performance.
