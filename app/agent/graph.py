from collections.abc import Callable
from typing import Any

from langgraph.graph import END, START, StateGraph

from app.agent.nodes.verifier import verifier_node
from app.agent.routing import route_after_verification
from app.agent.state import ResearchState


def build_research_graph(
    planner_node: Callable[..., Any],
    researcher_node: Callable[..., Any],
    evidence_processor_node: Callable[..., Any],
    synthesizer_node: Callable[..., Any],
):
    builder = StateGraph(ResearchState)

    builder.add_node(
        "planner",
        planner_node,
    )

    builder.add_node(
        "researcher",
        researcher_node,
    )

    builder.add_node(
        "evidence_processor",
        evidence_processor_node,
    )

    builder.add_node(
        "synthesizer",
        synthesizer_node,
    )

    builder.add_node(
        "verifier",
        verifier_node,
    )

    builder.add_edge(
        START,
        "planner",
    )

    builder.add_edge(
        "planner",
        "researcher",
    )

    builder.add_edge(
        "researcher",
        "evidence_processor",
    )

    builder.add_edge(
        "evidence_processor",
        "synthesizer",
    )

    builder.add_edge(
        "synthesizer",
        "verifier",
    )

    builder.add_conditional_edges(
        "verifier",
        route_after_verification,
        {
            "retry": "researcher",
            "finish": END,
        },
    )

    return builder.compile()
