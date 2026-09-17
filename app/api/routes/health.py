from typing import Any

from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    status,
)
from psycopg import Error as PsycopgError
from psycopg_pool import PoolClosed, PoolTimeout

router = APIRouter(tags=["health"])


async def _dependency_is_ready(dependency: Any) -> bool:
    if dependency is None:
        return False

    try:
        return bool(await dependency.ping())
    except (PsycopgError, PoolClosed, PoolTimeout):
        return False


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

    postgres_ok = await _dependency_is_ready(repository)

    redis_ok = await _dependency_is_ready(cache)

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
