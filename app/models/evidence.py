from typing import Literal

from pydantic import BaseModel, Field


class Evidence(BaseModel):
    source_id: str

    research_step_id: str

    source_type: Literal[
        "web",
        "document",
        "api",
    ] = "web"

    title: str

    url: str | None = None

    content: str

    relevance_score: float | None = Field(
        default=None,
        ge=0,
        le=1,
    )

    published_date: str | None = None
