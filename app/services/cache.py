import hashlib
import json

from redis.asyncio import Redis

from app.models.evidence import Evidence


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

        value = await self._redis.get(key)

        if value is None:
            return None

        payload = json.loads(value)

        return [Evidence.model_validate(item) for item in payload]

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

        await self._redis.set(
            key,
            json.dumps(payload),
            ex=self._ttl_seconds,
        )

    async def ping(self) -> bool:
        return bool(await self._redis.ping())
