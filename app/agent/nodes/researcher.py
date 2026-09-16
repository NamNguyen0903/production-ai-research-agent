import asyncio
from collections.abc import Callable, Coroutine
from typing import Any, Protocol

import httpx

from app.agent.state import ResearchState
from app.models.evidence import Evidence
from app.models.research import ResearchStep


class SearchToolProtocol(Protocol):
    async def search(
        self,
        query: str,
        research_step_id: str,
        max_results: int,
    ) -> list[Evidence]: ...


ResearcherNode = Callable[
    [ResearchState],
    Coroutine[Any, Any, dict[str, Any]],
]


async def mock_researcher_node(
    state: ResearchState,
) -> dict[str, Any]:
    return {
        "evidence": state.get(
            "evidence",
            [],
        ),
        "iteration": (state.get("iteration", 0) + 1),
    }


def create_researcher_node(
    search_tool: SearchToolProtocol,
    max_results: int,
) -> ResearcherNode:
    async def search_step(
        step: ResearchStep,
    ) -> tuple[
        ResearchStep,
        list[Evidence],
        str | None,
    ]:
        try:
            results = await search_tool.search(
                query=step.question,
                research_step_id=step.id,
                max_results=max_results,
            )

            updated_step = step.model_copy(
                update={
                    "status": "completed",
                }
            )

            return (
                updated_step,
                results,
                None,
            )

        except httpx.HTTPError as exc:
            updated_step = step.model_copy(
                update={
                    "status": "failed",
                }
            )

            error = f"{step.id}: {type(exc).__name__}: {exc}"

            return (
                updated_step,
                [],
                error,
            )

    async def researcher_node(
        state: ResearchState,
    ) -> dict[str, Any]:
        plan = state.get(
            "plan",
            [],
        )

        results = await asyncio.gather(*(search_step(step) for step in plan))

        evidence: list[Evidence] = []
        updated_plan: list[ResearchStep] = []
        new_errors: list[str] = []

        for (
            step,
            step_evidence,
            error,
        ) in results:
            updated_plan.append(step)

            evidence.extend(step_evidence)

            if error is not None:
                new_errors.append(error)

        return {
            "plan": updated_plan,
            "evidence": evidence,
            "iteration": (
                state.get(
                    "iteration",
                    0,
                )
                + 1
            ),
            "tool_calls": (
                state.get(
                    "tool_calls",
                    0,
                )
                + len(plan)
            ),
            "errors": [
                *state.get(
                    "errors",
                    [],
                ),
                *new_errors,
            ],
        }

    return researcher_node
