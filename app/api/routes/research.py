from uuid import uuid4

from fastapi import (
    APIRouter,
    HTTPException,
    Request,
)

from app.api.schemas import (
    ResearchMetrics,
    ResearchRequest,
    ResearchResponse,
    ResearchRunResponse,
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
    service = getattr(
        request.app.state,
        "research_service",
        None,
    )

    if service is None:
        raise HTTPException(
            status_code=503,
            detail=("Research service is not initialized."),
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
        "retry_queries": [],
        "max_tool_calls": (settings.max_tool_calls),
        "errors": [],
        "final_answer": None,
    }

    result = await service.run(
        run_id=run_id,
        initial_state=initial_state,
    )

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
            latency_ms=result.get(
                "_latency_ms",
                0,
            ),
        ),
    )


@router.get(
    "/{run_id}",
    response_model=ResearchRunResponse,
)
async def get_research_run(
    run_id: str,
    request: Request,
) -> ResearchRunResponse:
    repository = getattr(
        request.app.state,
        "run_repository",
        None,
    )

    if repository is None:
        raise HTTPException(
            status_code=503,
            detail=("Run persistence is not available."),
        )

    run = await repository.get_run(run_id)

    if run is None:
        raise HTTPException(
            status_code=404,
            detail="Research run not found.",
        )

    return ResearchRunResponse(
        **{
            **run,
            "run_id": str(run["run_id"]),
        }
    )
