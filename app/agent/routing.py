from typing import Literal

from app.agent.state import (
    ResearchState,
)


def route_after_verification(
    state: ResearchState,
) -> Literal[
    "retry",
    "finish",
]:
    verification = state.get("verification")

    if verification is not None and verification.passed:
        return "finish"

    iteration = state.get(
        "iteration",
        0,
    )

    max_iterations = state.get(
        "max_iterations",
        2,
    )

    if iteration >= max_iterations:
        return "finish"

    tool_calls = state.get(
        "tool_calls",
        0,
    )

    max_tool_calls = state.get(
        "max_tool_calls",
        15,
    )

    if tool_calls >= max_tool_calls:
        return "finish"

    retry_queries = state.get(
        "retry_queries",
        [],
    )

    if not retry_queries:
        return "finish"

    return "retry"
