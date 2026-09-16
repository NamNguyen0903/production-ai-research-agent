from datetime import datetime
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

    latency_ms: int


class ResearchResponse(BaseModel):
    run_id: str

    status: Literal["completed"]

    query: str

    plan: list[ResearchStep]

    answer: str | None

    sources: list[Evidence]

    verification: VerificationResult | None

    metrics: ResearchMetrics


class ResearchRunResponse(BaseModel):
    run_id: str

    query: str

    status: Literal[
        "running",
        "completed",
        "failed",
    ]

    started_at: datetime

    completed_at: datetime | None = None

    latency_ms: int | None = None

    tool_calls: int

    iterations: int

    sources_found: int

    verification_score: float | None = None

    error: str | None = None
