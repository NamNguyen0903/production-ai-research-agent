from uuid import uuid4

from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    status,
)

from app.api.schemas import (
    ResearchMetrics,
    ResearchRequest,
    ResearchResponse,
)
from app.core.config import get_settings

router = APIRouter(
    prefix="/v1/research",
    tags=["research"],
)


@router.post(
    "",
    response_model=ResearchResponse,
)
async def create_research(
    payload: ResearchRequest,
    request: Request,
) -> ResearchResponse:
    graph = getattr(
        request.app.state,
        "research_graph",
        None,
    )

    if graph is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Research graph is not initialized.",
        )

    settings = get_settings()

    run_id = str(uuid4())

    initial_state = {
        "run_id": run_id,
        "used_source_ids": [],
        "query": payload.query,
        "plan": [],
        "evidence": [],
        "draft_answer": None,
        "verification": None,
        "iteration": 0,
        "max_iterations": (payload.max_iterations or settings.max_iterations),
        "tool_calls": 0,
        "errors": [],
        "final_answer": None,
    }

    result = await graph.ainvoke(initial_state)

    evidence = result.get(
        "evidence",
        [],
    )

    return ResearchResponse(
        run_id=run_id,
        status="completed",
        query=payload.query,
        plan=result.get(
            "plan",
            [],
        ),
        answer=result.get("final_answer"),
        sources=evidence,
        verification=result.get("verification"),
        metrics=ResearchMetrics(
            tool_calls=result.get(
                "tool_calls",
                0,
            ),
            iterations=result.get(
                "iteration",
                0,
            ),
            sources_found=len(evidence),
        ),
    )
