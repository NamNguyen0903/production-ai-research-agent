from collections.abc import Callable, Coroutine
from typing import Any

from langchain_core.language_models.chat_models import (
    BaseChatModel,
)
from langchain_core.prompts import (
    ChatPromptTemplate,
)

from app.agent.prompts.synthesizer import (
    SYNTHESIZER_SYSTEM_PROMPT,
)
from app.agent.state import ResearchState
from app.models.synthesis import SynthesisResult

SynthesizerNode = Callable[
    [ResearchState],
    Coroutine[Any, Any, dict[str, Any]],
]


async def mock_synthesizer_node(
    state: ResearchState,
) -> dict[str, Any]:
    plan = state.get(
        "plan",
        [],
    )

    questions = "\n".join(f"- {step.question}" for step in plan)

    return {
        "draft_answer": (f"DAY 1 MOCK ANSWER\n\nResearch plan:\n{questions}"),
        "used_source_ids": [],
    }


def create_synthesizer_node(
    llm: BaseChatModel,
) -> SynthesizerNode:
    structured_llm = llm.with_structured_output(SynthesisResult)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                SYNTHESIZER_SYSTEM_PROMPT,
            ),
            (
                "human",
                """
Research question:

{query}

Evidence:

{evidence}
""",
            ),
        ]
    )

    chain = prompt | structured_llm

    async def synthesizer_node(
        state: ResearchState,
    ) -> dict[str, Any]:
        evidence = state.get(
            "evidence",
            [],
        )

        if not evidence:
            return {
                "draft_answer": (
                    "Insufficient evidence was "
                    "collected to answer the "
                    "research question."
                ),
                "used_source_ids": [],
            }

        evidence_text = "\n\n".join(
            (
                f"[{item.source_id}]\n"
                f"Title: {item.title}\n"
                f"URL: {item.url}\n"
                f"Evidence: {item.content}"
            )
            for item in evidence
        )

        result = await chain.ainvoke(
            {
                "query": state["query"],
                "evidence": evidence_text,
            }
        )

        if not isinstance(
            result,
            SynthesisResult,
        ):
            result = SynthesisResult.model_validate(result)

        return {
            "draft_answer": (result.answer),
            "used_source_ids": (result.used_source_ids),
        }

    return synthesizer_node
