import pytest

from app.agent.graph import build_research_graph
from app.agent.nodes.planner import mock_planner_node


@pytest.mark.asyncio
async def test_research_graph_runs_end_to_end():
    graph = build_research_graph(mock_planner_node)

    result = await graph.ainvoke(
        {
            "run_id": "test-run",
            "query": "Research small language models",
            "plan": [],
            "evidence": [],
            "draft_answer": None,
            "verification": None,
            "iteration": 0,
            "max_iterations": 2,
            "tool_calls": 0,
            "errors": [],
            "final_answer": None,
        }
    )

    assert len(result["plan"]) >= 2

    assert result["verification"] is not None
    assert result["verification"].passed is True

    assert result["final_answer"] is not None

    assert result["iteration"] == 1
