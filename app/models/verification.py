from pydantic import BaseModel, Field


class ClaimVerification(BaseModel):
    claim: str

    supported: bool

    evidence_ids: list[str] = Field(default_factory=list)

    reason: str


class VerificationResult(BaseModel):
    passed: bool

    coverage_score: float = Field(
        ge=0,
        le=1,
    )

    unsupported_claims: list[str] = Field(default_factory=list)

    claims: list[ClaimVerification] = Field(default_factory=list)
