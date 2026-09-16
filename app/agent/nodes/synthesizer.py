from typing import Any

from app.agent.state import ResearchState


async def synthesizer_node(
    state: ResearchState,
) -> dict[str, Any]:
    plan = state.get(
        "plan",
        [],
    )

    questions = "\n".join(f"- {step.question}" for step in plan)

    draft = (
        "DAY 1 MOCK ANSWER\n\n"
        "The research workflow executed successfully.\n\n"
        "Research plan:\n"
        f"{questions}"
    )

    return {
        "draft_answer": draft,
    }
