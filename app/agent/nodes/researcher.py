from typing import Any

from app.agent.state import ResearchState


async def researcher_node(
    state: ResearchState,
) -> dict[str, Any]:
    current_iteration = state.get(
        "iteration",
        0,
    )

    return {
        "evidence": state.get(
            "evidence",
            [],
        ),
        "iteration": current_iteration + 1,
    }
