import pytest

from app.models.evidence import Evidence
from app.services.cache import SearchCache


class FakeRedis:
    def __init__(self) -> None:
        self.storage: dict[str, str] = {}
        self.last_ttl: int | None = None

    async def get(
        self,
        key: str,
    ) -> str | None:
        return self.storage.get(key)

    async def set(
        self,
        key: str,
        value: str,
        *,
        ex: int | None = None,
    ) -> bool:
        self.storage[key] = value
        self.last_ttl = ex

        return True

    async def ping(self) -> bool:
        return True


def make_evidence() -> Evidence:
    return Evidence(
        source_id="raw-step-1-1",
        research_step_id="step-1",
        source_type="web",
        title="Example source",
        url="https://example.com/article",
        content="Example evidence content.",
        relevance_score=0.91,
        published_date="2026-09-16",
    )


@pytest.mark.asyncio
async def test_cache_returns_saved_evidence():
    redis = FakeRedis()

    cache = SearchCache(
        redis=redis,  # type: ignore[arg-type]
        ttl_seconds=900,
    )

    evidence = [make_evidence()]

    await cache.set(
        query="small language models",
        max_results=4,
        evidence=evidence,
    )

    result = await cache.get(
        query="small language models",
        max_results=4,
    )

    assert result is not None

    assert len(result) == 1

    assert result[0].source_id == "raw-step-1-1"

    assert result[0].research_step_id == "step-1"

    assert result[0].title == "Example source"

    assert result[0].relevance_score == 0.91


@pytest.mark.asyncio
async def test_cache_normalizes_query():
    redis = FakeRedis()

    cache = SearchCache(
        redis=redis,  # type: ignore[arg-type]
        ttl_seconds=900,
    )

    await cache.set(
        query="  Small Language Models  ",
        max_results=4,
        evidence=[make_evidence()],
    )

    result = await cache.get(
        query="small language models",
        max_results=4,
    )

    assert result is not None

    assert len(result) == 1


@pytest.mark.asyncio
async def test_cache_key_changes_with_max_results():
    redis = FakeRedis()

    cache = SearchCache(
        redis=redis,  # type: ignore[arg-type]
        ttl_seconds=900,
    )

    await cache.set(
        query="small language models",
        max_results=4,
        evidence=[make_evidence()],
    )

    result = await cache.get(
        query="small language models",
        max_results=5,
    )

    assert result is None


@pytest.mark.asyncio
async def test_cache_returns_none_on_miss():
    redis = FakeRedis()

    cache = SearchCache(
        redis=redis,  # type: ignore[arg-type]
        ttl_seconds=900,
    )

    result = await cache.get(
        query="query that does not exist",
        max_results=4,
    )

    assert result is None


@pytest.mark.asyncio
async def test_cache_applies_ttl():
    redis = FakeRedis()

    cache = SearchCache(
        redis=redis,  # type: ignore[arg-type]
        ttl_seconds=900,
    )

    await cache.set(
        query="small language models",
        max_results=4,
        evidence=[make_evidence()],
    )

    assert redis.last_ttl == 900


@pytest.mark.asyncio
async def test_cache_ping():
    redis = FakeRedis()

    cache = SearchCache(
        redis=redis,  # type: ignore[arg-type]
        ttl_seconds=900,
    )

    assert await cache.ping() is True
