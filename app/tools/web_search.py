from typing import Any, Protocol

import httpx
from pydantic import ValidationError

from app.models.evidence import Evidence
from app.tools.base import ToolExecutionError


class SearchCacheProtocol(Protocol):
    async def get(
        self,
        query: str,
        max_results: int,
    ) -> list[Evidence] | None: ...

    async def set(
        self,
        query: str,
        max_results: int,
        evidence: list[Evidence],
    ) -> None: ...


class WebSearchTool:
    def __init__(
        self,
        api_key: str,
        timeout_seconds: float = 15.0,
        cache: SearchCacheProtocol | None = None,
    ) -> None:
        self._api_key = api_key
        self._cache = cache

        self._client = httpx.AsyncClient(
            base_url="https://api.tavily.com",
            timeout=httpx.Timeout(timeout_seconds),
        )

    async def search(
        self,
        query: str,
        research_step_id: str,
        max_results: int = 4,
    ) -> list[Evidence]:
        if self._cache is not None:
            cached = await self._cache.get(
                query,
                max_results,
            )

            if cached is not None:
                return [
                    item.model_copy(
                        update={
                            "source_id": (f"raw-{research_step_id}-{index}"),
                            "research_step_id": (research_step_id),
                        }
                    )
                    for index, item in enumerate(
                        cached,
                        start=1,
                    )
                ]

        try:
            response = await self._client.post(
                "/search",
                headers={"Authorization": (f"Bearer {self._api_key}")},
                json={
                    "query": query,
                    "search_depth": "basic",
                    "max_results": max_results,
                    "topic": "general",
                    "include_answer": False,
                    "include_raw_content": False,
                    "include_images": False,
                    "include_published_date": True,
                },
            )

            response.raise_for_status()

            payload: dict[str, Any] = response.json()

            evidence: list[Evidence] = []

            for index, item in enumerate(
                payload.get("results", []),
                start=1,
            ):
                evidence.append(
                    Evidence(
                        source_id=(f"raw-{research_step_id}-{index}"),
                        research_step_id=research_step_id,
                        source_type="web",
                        title=item.get(
                            "title",
                            "Untitled source",
                        ),
                        url=item.get("url"),
                        content=item.get(
                            "content",
                            "",
                        ),
                        relevance_score=item.get("score"),
                        published_date=item.get("published_date"),
                    )
                )

            if self._cache is not None:
                await self._cache.set(
                    query,
                    max_results,
                    evidence,
                )

            return evidence

        except (
            httpx.HTTPError,
            ValueError,
            ValidationError,
        ) as exc:
            raise ToolExecutionError(
                f"Web search failed for query={query!r}: {exc}"
            ) from exc

    async def aclose(self) -> None:
        await self._client.aclose()
