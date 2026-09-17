from time import perf_counter
from typing import Any

from langfuse.langchain import (
    CallbackHandler,
)

from app.db.postgres import (
    ResearchRunRepository,
)


class ResearchService:
    def __init__(
        self,
        *,
        graph: Any,
        repository: (ResearchRunRepository | None),
        recursion_limit: int,
        langfuse_enabled: bool,
        langfuse_client: Any | None = None,
        langfuse_public_key: str | None = None,
    ) -> None:
        self._graph = graph
        self._repository = repository
        self._recursion_limit = recursion_limit
        self._langfuse_enabled = langfuse_enabled
        self._langfuse_client = langfuse_client
        self._langfuse_public_key = langfuse_public_key

    async def run(
        self,
        *,
        run_id: str,
        initial_state: dict[str, Any],
    ) -> dict[str, Any]:
        if self._repository is not None:
            await self._repository.create_run(
                run_id=run_id,
                query=initial_state["query"],
            )

        started = perf_counter()

        try:
            result = await self._invoke_graph(
                run_id=run_id,
                initial_state=initial_state,
            )

        except Exception as exc:
            if self._repository is not None:
                await self._repository.fail_run(
                    run_id=run_id,
                    error=str(exc),
                )

            raise

        latency_ms = int((perf_counter() - started) * 1000)

        verification = result.get("verification")

        score = verification.coverage_score if verification is not None else None

        evidence = result.get(
            "evidence",
            [],
        )

        if self._repository is not None:
            await self._repository.complete_run(
                run_id,
                latency_ms=latency_ms,
                tool_calls=result.get(
                    "tool_calls",
                    0,
                ),
                iterations=result.get(
                    "iteration",
                    0,
                ),
                sources_found=len(evidence),
                verification_score=score,
            )

        result["_latency_ms"] = latency_ms

        return result

    async def _invoke_graph(
        self,
        *,
        run_id: str,
        initial_state: dict[str, Any],
    ) -> dict[str, Any]:
        config: dict[str, Any] = {
            "configurable": {
                "thread_id": run_id,
            },
            "recursion_limit": (self._recursion_limit),
        }

        if not self._langfuse_enabled or self._langfuse_client is None:
            return await self._graph.ainvoke(
                initial_state,
                config=config,
            )

        handler = CallbackHandler(
            public_key=self._langfuse_public_key,
        )

        config["callbacks"] = [handler]

        with self._langfuse_client.start_as_current_observation(
            name="research-agent",
            as_type="agent",
            input={
                "run_id": run_id,
                "query": (initial_state["query"]),
            },
            metadata={
                "run_id": run_id,
            },
        ) as span:
            result = await self._graph.ainvoke(
                initial_state,
                config=config,
            )

            verification = result.get("verification")

            span.update(
                output={
                    "verification_passed": (
                        verification.passed if verification else None
                    ),
                    "tool_calls": (
                        result.get(
                            "tool_calls",
                            0,
                        )
                    ),
                    "iterations": (
                        result.get(
                            "iteration",
                            0,
                        )
                    ),
                }
            )

            return result
