from typing import Literal

from app.agent.state import ResearchState


def route_after_verification(
    state: ResearchState,
) -> Literal["retry", "finish"]:
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

    return "retry"
