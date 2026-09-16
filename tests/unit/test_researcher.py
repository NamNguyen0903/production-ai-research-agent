import pytest

from app.agent.nodes.researcher import (
    create_researcher_node,
)
from app.models.evidence import Evidence
from app.models.research import ResearchStep


class FakeSearchTool:
    def __init__(self):
        self.queries: list[str] = []

    async def search(
        self,
        query: str,
        research_step_id: str,
        max_results: int,
    ) -> list[Evidence]:
        self.queries.append(query)

        return [
            Evidence(
                source_id=(f"raw-{research_step_id}"),
                research_step_id=(research_step_id),
                source_type="web",
                title="Targeted result",
                url=(f"https://example.com/{research_step_id}"),
                content="Supporting evidence",
                relevance_score=0.9,
            )
        ]


@pytest.mark.asyncio
async def test_researcher_uses_targeted_retry_queries():
    search_tool = FakeSearchTool()

    researcher = create_researcher_node(
        search_tool=search_tool,
        max_results=3,
        max_tool_calls=10,
    )

    existing_evidence = Evidence(
        source_id="src-1",
        research_step_id="step-1",
        source_type="web",
        title="Existing source",
        url="https://example.com/original",
        content="Existing evidence",
        relevance_score=0.8,
    )

    state = {
        "query": "Research SLMs",
        "plan": [
            ResearchStep(
                id="step-1",
                question="Initial question?",
                rationale="Initial research",
                status="completed",
            )
        ],
        "evidence": [existing_evidence],
        "retry_queries": ["Phi benchmark official results"],
        "iteration": 1,
        "tool_calls": 3,
        "max_tool_calls": 10,
        "errors": [],
    }

    result = await researcher(state)

    assert search_tool.queries == ["Phi benchmark official results"]

    assert result["tool_calls"] == 4

    assert result["iteration"] == 2

    assert len(result["evidence"]) == 2

    assert result["retry_queries"] == []
