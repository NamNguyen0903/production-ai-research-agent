from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    status,
)

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
    }


@router.get("/ready")
async def ready(
    request: Request,
) -> dict:
    repository = getattr(
        request.app.state,
        "run_repository",
        None,
    )

    cache = getattr(
        request.app.state,
        "search_cache",
        None,
    )

    postgres_ok = await repository.ping() if repository is not None else False

    redis_ok = await cache.ping() if cache is not None else False

    ready_state = postgres_ok and redis_ok

    if not ready_state:
        raise HTTPException(
            status_code=(status.HTTP_503_SERVICE_UNAVAILABLE),
            detail={
                "status": "not_ready",
                "postgres": postgres_ok,
                "redis": redis_ok,
            },
        )

    return {
        "status": "ready",
        "postgres": "ok",
        "redis": "ok",
    }
