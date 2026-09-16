from typing import Any

from app.agent.state import ResearchState


async def evidence_processor_node(
    state: ResearchState,
) -> dict[str, Any]:
    return {
        "evidence": state.get(
            "evidence",
            [],
        )
    }
