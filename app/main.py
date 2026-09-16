from contextlib import asynccontextmanager
from typing import Any

import redis.asyncio as redis
from fastapi import FastAPI
from langgraph.checkpoint.postgres.aio import (
    AsyncPostgresSaver,
)

from app.agent.graph import build_research_graph
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
from app.core.config import get_settings
from app.db.factory import create_postgres_pool
from app.db.postgres import ResearchRunRepository
from app.llm.factory import create_chat_model
from app.services.cache import SearchCache
from app.services.research_service import ResearchService
from app.tools.web_search import WebSearchTool


def create_app(
    graph: Any | None = None,
) -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(
        app: FastAPI,
    ):
        postgres_pool = None
        redis_client = None
        web_search_tool = None
        checkpointer_context = None

        # Used by integration tests that inject
        # their own graph.
        if graph is not None:
            app.state.research_graph = graph

            app.state.research_service = ResearchService(
                graph=graph,
                repository=None,
                recursion_limit=(settings.graph_recursion_limit),
                langfuse_enabled=False,
            )

            yield

            app.state.research_graph = None
            app.state.research_service = None

            return

        try:
            # ---------------------------------
            # Infrastructure
            # ---------------------------------

            postgres_pool = create_postgres_pool(settings.postgres_uri)
            await postgres_pool.open()

            run_repository = ResearchRunRepository(postgres_pool)
            await run_repository.setup()

            app.state.run_repository = run_repository

            redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
            )

            search_cache = SearchCache(
                redis=redis_client,
                ttl_seconds=(settings.redis_cache_ttl_seconds),
            )

            app.state.search_cache = search_cache

            # ---------------------------------
            # LangGraph checkpointer
            # ---------------------------------

            checkpointer_context = AsyncPostgresSaver.from_conn_string(
                settings.postgres_uri
            )

            checkpointer = await checkpointer_context.__aenter__()

            await checkpointer.setup()

            # ---------------------------------
            # Agent nodes
            # ---------------------------------

            evidence_processor_node = create_evidence_processor_node(
                max_sources=settings.max_sources
            )

            if settings.llm_provider == "mock":
                planner_node = mock_planner_node
                researcher_node = mock_researcher_node
                synthesizer_node = mock_synthesizer_node
                verifier_node = mock_verifier_node

            else:
                if settings.tavily_api_key is None:
                    raise RuntimeError("TAVILY_API_KEY is required.")

                llm = create_chat_model(settings)

                web_search_tool = WebSearchTool(
                    api_key=(settings.tavily_api_key.get_secret_value()),
                    timeout_seconds=(settings.search_timeout_seconds),
                    cache=search_cache,
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

                synthesizer_node = create_synthesizer_node(llm=llm)

                verifier_node = create_verifier_node(
                    llm=llm,
                    min_coverage=(settings.verification_min_coverage),
                    max_targeted_queries=(settings.max_targeted_queries),
                )

            # ---------------------------------
            # Build graph
            # ---------------------------------

            research_graph = build_research_graph(
                planner_node=planner_node,
                researcher_node=researcher_node,
                evidence_processor_node=(evidence_processor_node),
                synthesizer_node=synthesizer_node,
                verifier_node=verifier_node,
                checkpointer=checkpointer,
            )

            app.state.research_graph = research_graph

            # ---------------------------------
            # Application service
            # ---------------------------------

            app.state.research_service = ResearchService(
                graph=research_graph,
                repository=run_repository,
                recursion_limit=(settings.graph_recursion_limit),
                langfuse_enabled=(settings.langfuse_enabled),
            )

            yield

        finally:
            # ---------------------------------
            # Graceful shutdown
            # ---------------------------------

            app.state.research_graph = None
            app.state.research_service = None

            if web_search_tool is not None:
                await web_search_tool.aclose()

            if redis_client is not None:
                await redis_client.aclose()

            if checkpointer_context is not None:
                await checkpointer_context.__aexit__(
                    None,
                    None,
                    None,
                )

            if postgres_pool is not None:
                await postgres_pool.close()

    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )

    application.include_router(health_router)
    application.include_router(research_router)

    return application


app = create_app()
