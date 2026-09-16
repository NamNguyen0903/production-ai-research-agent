from typing import Literal

from pydantic import BaseModel, Field

from app.models.evidence import Evidence
from app.models.research import ResearchStep
from app.models.verification import VerificationResult


class ResearchRequest(BaseModel):
    query: str = Field(
        min_length=3,
        max_length=2000,
    )

    max_iterations: int | None = Field(
        default=None,
        ge=1,
        le=5,
    )


class ResearchMetrics(BaseModel):
    tool_calls: int

    iterations: int

    sources_found: int


class ResearchResponse(BaseModel):
    run_id: str

    status: Literal["completed"]

    query: str

    plan: list[ResearchStep]

    answer: str | None

    sources: list[Evidence]

    verification: VerificationResult | None

    metrics: ResearchMetrics
