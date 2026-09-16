from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from app.agent.graph import (
    build_research_graph,
)
from app.agent.nodes.planner import (
    create_planner_node,
    mock_planner_node,
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


def create_app(
    graph: Any | None = None,
) -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(
        app: FastAPI,
    ):
        if graph is not None:
            app.state.research_graph = graph

        elif settings.llm_provider == "mock":
            app.state.research_graph = build_research_graph(mock_planner_node)

        else:
            llm = create_chat_model(settings)

            planner_node = create_planner_node(
                llm=llm,
                max_steps=(settings.max_research_steps),
            )

            app.state.research_graph = build_research_graph(planner_node)

        yield

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
