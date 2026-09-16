from pydantic import BaseModel, Field


class CitationValidationResult(BaseModel):
    valid: bool

    cited_source_ids: list[str] = Field(default_factory=list)

    invalid_source_ids: list[str] = Field(default_factory=list)


class ClaimVerification(BaseModel):
    claim: str

    supported: bool

    evidence_ids: list[str] = Field(default_factory=list)

    reason: str


class VerifierAssessment(BaseModel):
    claims: list[ClaimVerification] = Field(default_factory=list)

    missing_queries: list[str] = Field(default_factory=list)


class VerificationResult(BaseModel):
    passed: bool

    coverage_score: float = Field(
        ge=0.0,
        le=1.0,
    )

    citation_valid: bool = False

    cited_source_ids: list[str] = Field(default_factory=list)

    invalid_citations: list[str] = Field(default_factory=list)

    unsupported_claims: list[str] = Field(default_factory=list)

    claims: list[ClaimVerification] = Field(default_factory=list)

    missing_queries: list[str] = Field(default_factory=list)
