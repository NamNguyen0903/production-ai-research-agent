from typing import Literal

from pydantic import BaseModel, Field


class ResearchStep(BaseModel):
    id: str = Field(description="Unique identifier such as step-1.")

    question: str = Field(
        min_length=3,
        description="Specific research question that requires evidence.",
    )

    rationale: str = Field(
        min_length=3,
        description="Why this research step is necessary.",
    )

    status: Literal[
        "pending",
        "in_progress",
        "completed",
        "failed",
    ] = "pending"


class ResearchPlan(BaseModel):
    steps: list[ResearchStep] = Field(
        min_length=2,
        max_length=5,
        description="Ordered research steps.",
    )
