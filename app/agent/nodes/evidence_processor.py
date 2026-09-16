from urllib.parse import urlsplit, urlunsplit

from app.agent.state import ResearchState
from app.models.evidence import Evidence


def normalize_url(
    url: str | None,
) -> str | None:
    if not url:
        return None

    parts = urlsplit(url)

    normalized_path = parts.path.rstrip("/") or "/"

    return urlunsplit(
        (
            parts.scheme.lower(),
            parts.netloc.lower(),
            normalized_path,
            parts.query,
            "",
        )
    )


def evidence_dedup_key(
    evidence: Evidence,
) -> str:
    normalized_url = normalize_url(evidence.url)

    if normalized_url:
        return normalized_url

    return evidence.title.strip().lower()


def create_evidence_processor_node(
    max_sources: int,
):
    async def evidence_processor_node(
        state: ResearchState,
    ) -> dict:
        raw_evidence = state.get(
            "evidence",
            [],
        )

        deduplicated: dict[
            str,
            Evidence,
        ] = {}

        for evidence in raw_evidence:
            key = evidence_dedup_key(evidence)

            existing = deduplicated.get(key)

            if existing is None:
                deduplicated[key] = evidence
                continue

            existing_score = existing.relevance_score or 0.0

            new_score = evidence.relevance_score or 0.0

            if new_score > existing_score:
                deduplicated[key] = evidence

        ranked = sorted(
            deduplicated.values(),
            key=lambda evidence: evidence.relevance_score or 0.0,
            reverse=True,
        )

        ranked = ranked[:max_sources]

        final_evidence = [
            evidence.model_copy(update={"source_id": (f"src-{index}")})
            for index, evidence in enumerate(
                ranked,
                start=1,
            )
        ]

        return {
            "evidence": final_evidence,
        }

    return evidence_processor_node
