# Evaluation Analysis

## Scope and Method

This analysis uses only `evals/reports/latest.json`, generated at `2026-09-16T15:22:31.713616+00:00`, and the evaluation logic in `evals/run_eval.py`.

The dataset contains 30 research questions across seven categories:

| Category | Queries |
|---|---:|
| AI engineering | 8 |
| Technology landscape | 6 |
| Agents | 5 |
| Production AI | 4 |
| Company strategy | 3 |
| Technology comparison | 3 |
| Observability | 1 |

Each question defines a minimum source count of four or five and a minimum coverage score of `0.80`. A case counts as successful only when execution completes, the answer is non-empty, source and coverage thresholds pass, citations are valid, and verification passes.

## Recorded Results

| Metric | Value | Interpretation |
|---|---:|---|
| Total queries | 30 | Full dataset size |
| Completed queries | 30 | All requests returned a completed execution |
| Completion rate | 100.00% | No request-level failures in this run |
| Research success rate | 93.33% | 28 of 30 cases met every success condition |
| Citation validity | 93.33% | 28 of 30 answers contained recognized citations with no unknown IDs |
| Verification pass rate | 93.33% | Same two cases failed the combined citation/coverage gate |
| Average claim support | 100.00% | Mean backend coverage across completed cases was 1.0 |
| Tool success rate | 100.00% | `errors_count` was zero across 94 recorded calls |
| Retry rate | 0.00% | No case executed more than one research iteration |
| Average iterations | 1.00 | Every case stopped after initial research |
| Average tool calls | 3.13 | 94 calls across 30 cases |
| p50 latency | 13,250.50 ms | Median completed-request latency |
| p95 latency | 48,912.75 ms | Interpolated percentile calculated by the harness |

`avg_claim_support` is the mean of each response's backend-generated `coverage_score`. It should not be read as independent human factual-accuracy measurement: the underlying claim support decisions come from the LLM verifier.

## Failed Cases

### q01 — Current landscape of small language models

Recorded facts:

- Execution completed with a non-empty answer.
- 12 sources were returned, satisfying the five-source requirement.
- Coverage was `1.0`; no unsupported claims were recorded.
- Three tool calls completed with zero tool errors.
- Citation validation and overall verification failed.
- `invalid_citations` was empty.

Classification: **citations**, specifically missing recognized citations. In the validator, an empty cited-ID set produces `citation_valid=false`; an invented ID would instead appear in `invalid_citations`.

The report does not retain the answer text, so it cannot establish why the synthesizer omitted citations. It does show that search quantity, coverage, tool errors, retry exhaustion, and latency were not the recorded failure conditions.

Realistic improvement: add a bounded citation-repair or resynthesis branch for the case where evidence and semantic coverage are sufficient but no citations were emitted. Also store citation counts or a redacted answer artifact in future evaluation reports to improve diagnosis.

### q05 — Google's strategy for deploying efficient AI models

Recorded facts:

- Execution completed with a non-empty answer.
- Nine sources were returned, satisfying the five-source requirement.
- Coverage was `1.0`; no unsupported claims were recorded.
- Three tool calls completed with zero tool errors.
- Citation validation and overall verification failed.
- `invalid_citations` was empty.

Classification: **citations**, again consistent with no recognized `[src-x]` citations. There is no evidence in the report for a search-quality, insufficient-evidence, tool-error, or latency failure.

Realistic improvement: use the same citation-repair path as q01 and add a regression evaluation that asserts a cited answer whenever evidence is non-empty.

## Weak but Successful Cases

The report does not mark any case as having insufficient evidence, tool errors, unsupported claims, retries, or retry exhaustion. The main weak signal outside the two failures is latency:

| Query | Topic | Latency |
|---|---|---:|
| q11 | Reducing LLM inference latency | 49,770 ms |
| q21 | Caching strategies for LLM/agent apps | 48,951 ms |
| q22 | Reducing hallucinations | 48,866 ms |
| q12 | LLM inference batching | 46,287 ms |

All four cases passed with three tool calls, 12 sources, valid citations, coverage `1.0`, and no tool errors. The report contains only end-to-end latency, so it cannot attribute the delay to planning, Tavily, synthesis, verification, provider queueing, or local infrastructure.

Realistic improvement: record per-node and per-tool latency, cache-hit status, and LLM usage in the evaluation output. Those measurements would identify whether parallel search, model calls, or provider variance dominates the tail.

## Retry Analysis

No query retried. This is not evidence that retry is broken: 28 cases passed immediately, while q01 and q05 had full semantic coverage and no missing-evidence queries. The current router retries only when verification fails **and** `retry_queries` is non-empty. Missing citations with otherwise supported claims therefore finish without another search, which avoids a useless retrieval retry but leaves no citation-repair mechanism.

Targeted retry behavior is covered separately by unit tests; it was simply not exercised by this recorded dataset run.

## Conclusions

The run demonstrates reliable completion and tool execution across this dataset, with 28 of 30 cases meeting every evaluation gate. The two failures are narrow and reproducible at the metric level: evidence and coverage passed, but citations were absent. The highest-value quality improvement is citation repair, while the highest-value measurement improvement is per-stage latency and richer failure artifacts.

These results are evidence for this one 30-query run, not for production scale, general factual accuracy, uptime, or performance under load.
