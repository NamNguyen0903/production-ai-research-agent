from pydantic import BaseModel, Field


class Evidence(BaseModel):
    source_id: str

    title: str

    url: str | None = None

    content: str

    relevance_score: float | None = Field(
        default=None,
        ge=0,
        le=1,
    )
