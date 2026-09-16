from app.agent.validators.citations import (
    extract_citation_ids,
    validate_citations,
)
from app.models.evidence import Evidence


def make_evidence(
    source_id: str,
) -> Evidence:
    return Evidence(
        source_id=source_id,
        research_step_id="step-1",
        source_type="web",
        title="Example",
        url="https://example.com",
        content="Example evidence",
        relevance_score=0.9,
    )


def test_extract_citations():
    answer = "Claim A [src-1]. Claim B [src-2][src-1]."

    assert extract_citation_ids(answer) == [
        "src-1",
        "src-2",
    ]


def test_valid_citations():
    evidence = [
        make_evidence("src-1"),
        make_evidence("src-2"),
    ]

    result = validate_citations(
        "Claim [src-1] [src-2].",
        evidence,
    )

    assert result.valid is True
    assert result.invalid_source_ids == []


def test_invalid_citation_is_detected():
    evidence = [make_evidence("src-1")]

    result = validate_citations(
        "Claim [src-99].",
        evidence,
    )

    assert result.valid is False

    assert result.invalid_source_ids == ["src-99"]


def test_missing_citations_is_invalid():
    evidence = [make_evidence("src-1")]

    result = validate_citations(
        "A factual report without citations.",
        evidence,
    )

    assert result.valid is False
