import pytest

from app.agent.nodes.evidence_processor import (
    create_evidence_processor_node,
)
from app.models.evidence import Evidence


@pytest.mark.asyncio
async def test_evidence_is_deduplicated_and_ranked():
    node = create_evidence_processor_node(max_sources=10)

    state = {
        "evidence": [
            Evidence(
                source_id="raw-1",
                research_step_id="step-1",
                title="Source A",
                url="https://example.com/a",
                content="Older result",
                relevance_score=0.5,
            ),
            Evidence(
                source_id="raw-2",
                research_step_id="step-2",
                title="Source A duplicate",
                url="https://example.com/a/",
                content="Better result",
                relevance_score=0.9,
            ),
            Evidence(
                source_id="raw-3",
                research_step_id="step-1",
                title="Source B",
                url="https://example.com/b",
                content="Another source",
                relevance_score=0.7,
            ),
        ]
    }

    result = await node(state)

    evidence = result["evidence"]

    assert len(evidence) == 2

    assert evidence[0].relevance_score == 0.9

    assert evidence[0].source_id == "src-1"

    assert evidence[1].source_id == "src-2"
