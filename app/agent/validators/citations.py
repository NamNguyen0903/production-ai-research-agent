import re

from app.models.evidence import Evidence
from app.models.verification import (
    CitationValidationResult,
)

CITATION_PATTERN = re.compile(r"\[(src-\d+)\]")


def extract_citation_ids(
    answer: str,
) -> list[str]:
    matches = CITATION_PATTERN.findall(answer)

    return list(dict.fromkeys(matches))


def validate_citations(
    answer: str,
    evidence: list[Evidence],
) -> CitationValidationResult:
    cited_ids = extract_citation_ids(answer)

    available_ids = {item.source_id for item in evidence}

    invalid_ids = [
        source_id for source_id in cited_ids if source_id not in available_ids
    ]

    valid = bool(cited_ids) and not invalid_ids

    return CitationValidationResult(
        valid=valid,
        cited_source_ids=cited_ids,
        invalid_source_ids=invalid_ids,
    )
