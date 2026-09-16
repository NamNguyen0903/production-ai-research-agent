from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from app.agent.graph import (
    build_research_graph,
)
from app.agent.nodes.evidence_processor import (
    create_evidence_processor_node,
)
from app.agent.nodes.planner import (
    create_planner_node,
    mock_planner_node,
)
from app.agent.nodes.researcher import (
    create_researcher_node,
    mock_researcher_node,
)
from app.agent.nodes.synthesizer import (
    create_synthesizer_node,
    mock_synthesizer_node,
)
from app.agent.nodes.verifier import (
    create_verifier_node,
    mock_verifier_node,
)
from app.api.routes.health import (
    router as health_router,
)
from app.api.routes.research import (
    router as research_router,
)
from app.core.config import (
    get_settings,
)
from app.llm.factory import (
    create_chat_model,
)
from app.tools.web_search import WebSearchTool


def create_app(
    graph: Any | None = None,
) -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(
        app: FastAPI,
    ):
        web_search_tool = None

        if graph is not None:
            app.state.research_graph = graph

        elif settings.llm_provider == "mock":
            app.state.research_graph = build_research_graph(
                planner_node=mock_planner_node,
                researcher_node=mock_researcher_node,
                evidence_processor_node=(
                    create_evidence_processor_node(max_sources=(settings.max_sources))
                ),
                synthesizer_node=(mock_synthesizer_node),
                verifier_node=mock_verifier_node,
            )

        else:
            if settings.tavily_api_key is None:
                raise RuntimeError("TAVILY_API_KEY is required.")

            llm = create_chat_model(settings)

            web_search_tool = WebSearchTool(
                api_key=(settings.tavily_api_key.get_secret_value()),
                timeout_seconds=(settings.search_timeout_seconds),
            )

            planner_node = create_planner_node(
                llm=llm,
                max_steps=(settings.max_research_steps),
            )

            researcher_node = create_researcher_node(
                search_tool=web_search_tool,
                max_results=(settings.max_search_results),
                max_tool_calls=(settings.max_tool_calls),
            )

            evidence_processor_node = create_evidence_processor_node(
                max_sources=(settings.max_sources)
            )

            synthesizer_node = create_synthesizer_node(llm=llm)

            verifier_node = create_verifier_node(
                llm=llm,
                min_coverage=settings.verification_min_coverage,
                max_targeted_queries=settings.max_targeted_queries,
            )

            app.state.research_graph = build_research_graph(
                planner_node=planner_node,
                researcher_node=researcher_node,
                evidence_processor_node=evidence_processor_node,
                synthesizer_node=synthesizer_node,
                verifier_node=verifier_node,
            )

        yield

        if web_search_tool is not None:
            await web_search_tool.aclose()

        app.state.research_graph = None

    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )

    application.include_router(health_router)

    application.include_router(research_router)

    return application


app = create_app()
