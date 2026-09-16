from typing import Any

from app.agent.state import ResearchState
from app.models.verification import VerificationResult


async def verifier_node(
    state: ResearchState,
) -> dict[str, Any]:
    draft = state.get("draft_answer")

    result = VerificationResult(
        passed=True,
        coverage_score=0.0,
        unsupported_claims=[],
        claims=[],
    )

    return {
        "verification": result,
        "final_answer": draft,
    }
