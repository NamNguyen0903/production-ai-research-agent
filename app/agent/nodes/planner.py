from collections.abc import Callable, Coroutine
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

from app.agent.prompts.planner import PLANNER_SYSTEM_PROMPT
from app.agent.state import ResearchState
from app.models.research import ResearchPlan, ResearchStep

PlannerNode = Callable[
    [ResearchState],
    Coroutine[Any, Any, dict[str, Any]],
]


def create_planner_node(
    llm: BaseChatModel,
    max_steps: int,
) -> PlannerNode:
    structured_llm = llm.with_structured_output(ResearchPlan)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                PLANNER_SYSTEM_PROMPT,
            ),
            (
                "human",
                "{query}",
            ),
        ]
    )

    chain = prompt | structured_llm

    async def planner_node(
        state: ResearchState,
    ) -> dict[str, Any]:
        result = await chain.ainvoke(
            {
                "query": state["query"],
                "max_steps": max_steps,
            }
        )

        if isinstance(result, ResearchPlan):
            plan = result
        else:
            plan = ResearchPlan.model_validate(result)

        return {
            "plan": plan.steps[:max_steps],
        }

    return planner_node


async def mock_planner_node(
    state: ResearchState,
) -> dict[str, Any]:
    query = state["query"]

    return {
        "plan": [
            ResearchStep(
                id="step-1",
                question=(f"What are the key facts required to answer: {query}?"),
                rationale=("Establish the core factual context."),
                status="pending",
            ),
            ResearchStep(
                id="step-2",
                question=("What reliable evidence supports the main findings?"),
                rationale=("Collect evidence for verification."),
                status="pending",
            ),
        ]
    }
