# Interview Q&A

## 1. Why did you need an agent?

The task requires multiple dependent actions: plan the question, search several evidence gaps, merge sources, synthesize, verify, and sometimes research again. A single prompt cannot reliably control those tool calls, preserve typed state, or enforce bounded recovery.

## 2. Why did you choose LangGraph?

The workflow has explicit nodes and a conditional cycle. LangGraph provides typed state transitions, conditional routing, PostgreSQL checkpoints, callbacks, and recursion protection while keeping each node independently testable.

## 3. Why not use a custom `while` loop?

A loop could implement the basic retry, but I would also have to design checkpoint storage, routing conventions, resumable state, tracing hooks, and graph-level safety. LangGraph gives those orchestration primitives while my code remains focused on research behavior.

## 4. What is stored in `ResearchState`?

It stores the run ID and query; typed plan and evidence; draft and final answers; used source IDs; verification and retry queries; iteration and tool-call counters with their limits; and accumulated tool errors.

## 5. Why use structured LLM output?

Planner, synthesis, and verifier responses cross application boundaries. Pydantic validates their shape and constraints early, so the graph does not depend on parsing arbitrary prose or silently accepting missing fields.

## 6. How do you prevent infinite loops?

Routing stops when verification passes, there are no targeted queries, the iteration budget is exhausted, or the tool budget is exhausted. LangGraph's independent recursion limit is passed on every invocation as a final graph-level guard.

## 7. What happens if Tavily fails?

HTTP, timeout, decoding, and evidence-validation failures become `ToolExecutionError`. The researcher marks only that plan step failed, records an abstracted error, and keeps results from sibling searches. The graph can still synthesize from partial evidence.

## 8. Why run searches asynchronously?

Planner steps are independent and I/O-bound. `asyncio.gather` overlaps their network waits, reducing wall-clock latency compared with serial execution while preserving one result and status per step.

## 9. Why use Redis?

Equivalent web searches may occur across runs or retries. A short-lived cache avoids repeated external calls and latency. It is an optimization: Redis read failures become misses and write failures do not discard live Tavily results.

## 10. What exactly is cached?

Serialized Tavily evidence is cached under a SHA-256 key derived from the normalized query and `max_results`. The default TTL is 900 seconds.

## 11. Why use PostgreSQL?

It provides durable run metadata and supports the official LangGraph PostgreSQL checkpointer. The app uses an async connection pool and closes it through FastAPI lifespan management.

## 12. What is the difference between `research_runs` and LangGraph checkpoints?

`research_runs` is my stable, API-facing summary: status, timestamps, latency, usage counts, verification score, and errors. Checkpoints are framework-owned snapshots of detailed graph state. Separating them avoids coupling the API to LangGraph's internal schema.

## 13. How do you resume a run?

The graph checkpoints state under `thread_id=run_id`, so the storage foundation for resumption exists. This v1 API does not expose a resume endpoint; it only starts a run and retrieves metadata, so I would not claim public resume support yet.

## 14. How do you validate citations?

A regex extracts unique IDs matching `[src-<number>]`. Python compares them with the processed evidence IDs. Validation requires at least one citation and rejects any unknown ID.

## 15. Can the LLM invent source IDs?

It can emit them, but they cannot pass unchecked. The citation validator flags unknown cited IDs, and the verifier node filters claim-level evidence IDs against the available set before calculating support.

## 16. How is `coverage_score` calculated?

After filtering verifier evidence IDs, the backend counts supported claims and divides by total extracted claims. If there are no claims, the score is zero. The LLM never returns the final coverage number.

## 17. Why use targeted retry?

The existing evidence may already support most of the answer. Searching only verifier-generated missing-evidence queries avoids repeating successful work, preserves useful sources, and reduces external calls.

## 18. What if the retry still fails?

The graph stops when it reaches the iteration or tool budget, when the recursion guard triggers, or when no further missing query exists. It returns the latest answer with `verification.passed=false`, so the caller can distinguish completed execution from verified output.

## 19. What does `max_tool_calls` solve?

It caps external search usage even if the planner or verifier proposes many queries. The researcher calculates remaining calls and executes only that many active steps.

## 20. What does `recursion_limit` solve?

It is a graph-level safety net against unexpected routing cycles or future graph changes. It complements application budgets rather than replacing them.

## 21. How do you evaluate the agent?

The harness sends 30 categorized questions to the real HTTP API and checks completion, non-empty output, per-case source minimums, coverage minimums, citation validity, and verification pass. It aggregates success, tool errors, retries, usage, and latency percentiles into JSON.

## 22. What does Langfuse provide?

When enabled, it wraps the run in a root agent observation and receives callbacks for LangGraph and LLM activity. The root output records verification, tool calls, and iterations. Custom Tavily HTTP calls are not yet dedicated child spans, which is an observability gap I would address next.

## 23. What are the biggest limitations?

Search quality depends on Tavily; semantic verification is LLM-based; ranking does not independently score authority; web content creates prompt-injection risk; the API is synchronous and unauthenticated; and the 30-query benchmark is too small to establish general quality or production scale.

## 24. What would you improve next?

First I would add citation repair because the recorded failures had evidence but omitted citations. Then I would add stronger source-quality scoring, background execution, explicit tool/cost/latency traces, authentication and rate limiting, and a larger repeated benchmark.

## 25. How is this different from your Enterprise RAG project?

Based on this repository alone, the defensible distinction is that this system performs live web research with planning, parallel tool use, verification, and a conditional retry loop. A conventional enterprise RAG system usually retrieves from an indexed private corpus and focuses more on ingestion, access control, chunking, and retrieval. I would compare the other project's actual implementation before making more specific claims.
