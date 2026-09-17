# 3–5 Minute Interview Explanation

I built a production-oriented AI research agent that turns an open-ended question into a cited, verified web research response. The problem I wanted to solve was that a single LLM call is not reliable enough for current research: it may not have fresh information, it can invent sources, and it gives me no controlled way to recover when evidence is incomplete.

The entry point is a FastAPI endpoint. A `ResearchService` creates a run ID, persists a running record in PostgreSQL, and invokes a LangGraph workflow. I chose LangGraph because the system is a real state machine: it has planning, research, evidence processing, synthesis, verification, and a conditional retry edge. LangGraph gives me explicit state transitions, PostgreSQL checkpoints, callback integration, and a recursion limit without building all of that around a custom loop.

The planner uses structured Pydantic output to break the question into two to five focused research steps. The researcher executes those steps concurrently with `asyncio.gather`, so independent web searches do not wait for each other. Each search goes through a Tavily adapter and a Redis cache. The cache key uses normalized query text and the requested result count, not the research step ID, because the search result itself is reusable. On a cache hit, I copy the evidence and remap it to the current step.

Next, the evidence processor normalizes URLs, removes duplicates, ranks results using the provider relevance score, limits the total source count, and assigns stable IDs such as `src-1`. The synthesizer receives only that evidence and is instructed to cite those exact IDs.

Verification has two layers. First, citation validation is deterministic: Python extracts every `[src-x]` token and checks whether it exists in the evidence set. I do not use an LLM for a membership test because code is cheaper, faster, and exact. Second, an LLM verifier evaluates factual claims against the evidence and returns typed claim decisions. The backend filters any invented evidence IDs and calculates coverage itself as supported claims divided by total claims. That prevents the model from choosing its own score.

If verification fails because evidence is missing, the verifier creates a small set of targeted search queries. The graph searches only those gaps, keeps the evidence it already has, processes the merged evidence, and synthesizes again. It does not rerun the entire original plan.

I added three independent loop safeguards: a maximum research-iteration count, a maximum tool-call budget, and LangGraph's recursion limit. One Tavily failure is converted into a tool error for that step, while other concurrent searches can still succeed. Redis is treated as an optimization, so cache failures fall back to live search.

For persistence, I use PostgreSQL in two different ways. My own `research_runs` table stores stable API metadata such as status, latency, tool calls, source count, and verification score. LangGraph's PostgreSQL checkpointer stores detailed execution state keyed by the same run ID as `thread_id`. Keeping those separate prevents my API contract from depending on framework tables.

Langfuse is optional. It creates a root research observation and receives LangChain/LangGraph callbacks for graph and LLM activity. The root output includes verification, iteration, and tool-call metrics. A current limitation is that the custom Tavily HTTP call does not yet have its own dedicated child span.

I evaluated the project on 30 research questions. In the recorded run, all 30 completed; research success, citation validity, and verification pass rate were each 93.33%, tool success was 100%, median latency was 13.25 seconds, and p95 was 48.91 seconds. The two failures had enough sources and full verifier coverage but no recognized citations. That suggests a citation-repair or resynthesis branch is a better next step than more searching.

The main tradeoff is that semantic verification still depends on an LLM, while deterministic rules handle only what can be checked exactly. Other limitations are provider-dependent search quality, basic relevance ranking, prompt-injection risk from web content, synchronous HTTP execution, and a relatively small benchmark. My next improvements would be stronger source-quality scoring, citation repair, background jobs, per-node cost and latency tracking, explicit tool spans, and security controls such as authentication and rate limiting.
