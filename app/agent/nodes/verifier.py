from collections.abc import (
    Callable,
    Coroutine,
)
from typing import Any

from langchain_core.language_models.chat_models import (
    BaseChatModel,
)
from langchain_core.prompts import (
    ChatPromptTemplate,
)

from app.agent.prompts.verifier import (
    VERIFIER_SYSTEM_PROMPT,
)
from app.agent.state import ResearchState
from app.agent.validators.citations import (
    validate_citations,
)
from app.models.verification import (
    ClaimVerification,
    VerificationResult,
    VerifierAssessment,
)

VerifierNode = Callable[
    [ResearchState],
    Coroutine[Any, Any, dict[str, Any]],
]


async def mock_verifier_node(
    state: ResearchState,
) -> dict[str, Any]:
    draft = state.get("draft_answer")

    result = VerificationResult(
        passed=True,
        coverage_score=0.0,
    )

    return {
        "verification": result,
        "retry_queries": [],
        "final_answer": draft,
    }


def create_verifier_node(
    llm: BaseChatModel,
    min_coverage: float,
    max_targeted_queries: int,
) -> VerifierNode:
    structured_llm = llm.with_structured_output(VerifierAssessment)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                VERIFIER_SYSTEM_PROMPT,
            ),
            (
                "human",
                """
Original research question:

{query}

Draft answer:

{answer}

Evidence:

{evidence}
""",
            ),
        ]
    )

    chain = prompt | structured_llm

    async def verifier_node(
        state: ResearchState,
    ) -> dict[str, Any]:
        answer = state.get("draft_answer") or ""

        evidence = state.get(
            "evidence",
            [],
        )

        citation_result = validate_citations(
            answer,
            evidence,
        )

        if not evidence:
            result = VerificationResult(
                passed=False,
                coverage_score=0.0,
                citation_valid=False,
                unsupported_claims=["No evidence was available."],
                missing_queries=[state["query"]],
            )

            return {
                "verification": result,
                "retry_queries": [state["query"]],
                "final_answer": answer,
            }

        evidence_text = "\n\n".join(
            (
                f"[{item.source_id}]\n"
                f"Title: {item.title}\n"
                f"URL: {item.url}\n"
                f"Evidence: "
                f"{item.content[:2500]}"
            )
            for item in evidence
        )

        assessment = await chain.ainvoke(
            {
                "query": state["query"],
                "answer": answer,
                "evidence": evidence_text,
                "max_targeted_queries": (max_targeted_queries),
            }
        )

        if not isinstance(
            assessment,
            VerifierAssessment,
        ):
            assessment = VerifierAssessment.model_validate(assessment)

        valid_source_ids = {item.source_id for item in evidence}

        claims: list[ClaimVerification] = []

        for claim in assessment.claims:
            valid_claim_ids = [
                source_id
                for source_id in claim.evidence_ids
                if source_id in valid_source_ids
            ]

            supported = claim.supported and bool(valid_claim_ids)

            claims.append(
                claim.model_copy(
                    update={
                        "supported": supported,
                        "evidence_ids": (valid_claim_ids),
                    }
                )
            )

        supported_count = sum(claim.supported for claim in claims)

        coverage_score = supported_count / len(claims) if claims else 0.0

        unsupported_claims = [claim.claim for claim in claims if not claim.supported]

        missing_queries = list(dict.fromkeys(assessment.missing_queries))[
            :max_targeted_queries
        ]

        passed = citation_result.valid and coverage_score >= min_coverage

        verification = VerificationResult(
            passed=passed,
            coverage_score=(coverage_score),
            citation_valid=(citation_result.valid),
            cited_source_ids=(citation_result.cited_source_ids),
            invalid_citations=(citation_result.invalid_source_ids),
            unsupported_claims=(unsupported_claims),
            claims=claims,
            missing_queries=(missing_queries),
        )

        return {
            "verification": verification,
            "retry_queries": ([] if passed else missing_queries),
            "used_source_ids": (citation_result.cited_source_ids),
            "final_answer": answer,
        }

    return verifier_node
