from typing import Any

import httpx

from app.models.evidence import Evidence


class WebSearchTool:
    def __init__(
        self,
        api_key: str,
        timeout_seconds: float = 15.0,
    ) -> None:
        self._api_key = api_key

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
                    research_step_id=(research_step_id),
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

        return evidence

    async def aclose(self) -> None:
        await self._client.aclose()
