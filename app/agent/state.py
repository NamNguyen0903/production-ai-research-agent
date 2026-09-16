from typing import TypedDict

from app.models.evidence import Evidence
from app.models.research import ResearchStep
from app.models.verification import VerificationResult


class ResearchState(TypedDict, total=False):
    run_id: str
    query: str

    plan: list[ResearchStep]
    evidence: list[Evidence]

    draft_answer: str | None
    used_source_ids: list[str]

    verification: VerificationResult | None

    retry_queries: list[str]

    iteration: int
    max_iterations: int

    tool_calls: int
    max_tool_calls: int

    errors: list[str]

    final_answer: str | None
