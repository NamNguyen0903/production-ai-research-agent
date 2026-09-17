import hashlib
import json
import logging

from pydantic import ValidationError
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.models.evidence import Evidence

logger = logging.getLogger(__name__)


class SearchCache:
    def __init__(
        self,
        redis: Redis,
        ttl_seconds: int,
    ) -> None:
        self._redis = redis
        self._ttl_seconds = ttl_seconds

    def _key(
        self,
        query: str,
        max_results: int,
    ) -> str:
        normalized = query.strip().lower()

        raw_key = f"{normalized}:{max_results}"

        digest = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

        return f"research-agent:web-search:{digest}"

    async def get(
        self,
        query: str,
        max_results: int,
    ) -> list[Evidence] | None:
        key = self._key(
            query,
            max_results,
        )

        try:
            value = await self._redis.get(key)
        except RedisError:
            logger.warning(
                "Redis cache read failed; continuing with a cache miss.",
                exc_info=True,
            )
            return None

        if value is None:
            return None

        try:
            payload = json.loads(value)
            return [Evidence.model_validate(item) for item in payload]
        except (json.JSONDecodeError, TypeError, ValidationError):
            logger.warning(
                "Redis cache entry was invalid; continuing with a cache miss.",
                exc_info=True,
            )
            return None

    async def set(
        self,
        query: str,
        max_results: int,
        evidence: list[Evidence],
    ) -> None:
        key = self._key(
            query,
            max_results,
        )

        payload = [item.model_dump(mode="json") for item in evidence]

        try:
            await self._redis.set(
                key,
                json.dumps(payload),
                ex=self._ttl_seconds,
            )
        except RedisError:
            logger.warning(
                "Redis cache write failed; returning uncached search results.",
                exc_info=True,
            )

    async def ping(self) -> bool:
        try:
            return bool(await self._redis.ping())
        except RedisError:
            return False
