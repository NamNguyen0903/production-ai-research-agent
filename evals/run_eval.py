import argparse
import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from typing import Any

import httpx

BASE_DIR = Path(__file__).resolve().parent

DEFAULT_DATASET = (
    BASE_DIR
    / "datasets"
    / "research_questions.json"
)

REPORT_DIR = (
    BASE_DIR
    / "reports"
)


def percentile(
    values: list[float],
    percentile_value: float,
) -> float:
    if not values:
        return 0.0

    ordered = sorted(values)

    if len(ordered) == 1:
        return ordered[0]

    index = (
        percentile_value
        / 100
        * (len(ordered) - 1)
    )

    lower = int(index)
    upper = min(
        lower + 1,
        len(ordered) - 1,
    )

    fraction = index - lower

    return (
        ordered[lower]
        + (
            ordered[upper]
            - ordered[lower]
        )
        * fraction
    )


async def evaluate_case(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    case: dict[str, Any],
) -> dict[str, Any]:
    async with semaphore:
        try:
            response = await client.post(
                "/v1/research",
                json={
                    "query": case[
                        "question"
                    ],
                    "max_iterations": 2,
                },
            )

        except httpx.HTTPError as exc:
            return {
                "id": case["id"],
                "category": case[
                    "category"
                ],
                "question": case[
                    "question"
                ],
                "completed": False,
                "success": False,
                "error": str(exc),
            }

    if response.status_code != 200:
        return {
            "id": case["id"],
            "category": case[
                "category"
            ],
            "question": case[
                "question"
            ],
            "completed": False,
            "success": False,
            "http_status": (
                response.status_code
            ),
            "error": response.text,
        }

    body = response.json()

    verification = (
        body.get("verification")
        or {}
    )

    metrics = (
        body.get("metrics")
        or {}
    )

    sources = (
        body.get("sources")
        or []
    )

    answer = (
        body.get("answer")
        or ""
    ).strip()

    completed = (
        body.get("status")
        == "completed"
    )

    coverage_score = float(
        verification.get(
            "coverage_score",
            0.0,
        )
        or 0.0
    )

    citation_valid = bool(
        verification.get(
            "citation_valid",
            False,
        )
    )

    verification_passed = bool(
        verification.get(
            "passed",
            False,
        )
    )

    min_sources = int(
        case.get(
            "min_sources",
            1,
        )
    )

    min_coverage = float(
        case.get(
            "min_coverage",
            0.8,
        )
    )

    source_requirement_passed = (
        len(sources)
        >= min_sources
    )

    coverage_requirement_passed = (
        coverage_score
        >= min_coverage
    )

    success = (
        completed
        and bool(answer)
        and source_requirement_passed
        and coverage_requirement_passed
        and citation_valid
        and verification_passed
    )

    return {
        "id": case["id"],
        "category": case[
            "category"
        ],
        "question": case[
            "question"
        ],

        "completed": completed,
        "success": success,

        "answer_nonempty": bool(
            answer
        ),

        "sources_found": len(
            sources
        ),

        "source_requirement_passed": (
            source_requirement_passed
        ),

        "coverage_score": (
            coverage_score
        ),

        "coverage_requirement_passed": (
            coverage_requirement_passed
        ),

        "citation_valid": (
            citation_valid
        ),

        "verification_passed": (
            verification_passed
        ),

        "tool_calls": int(
            metrics.get(
                "tool_calls",
                0,
            )
        ),

        "errors_count": int(
            metrics.get(
                "errors_count",
                0,
            )
        ),

        "iterations": int(
            metrics.get(
                "iterations",
                0,
            )
        ),

        "latency_ms": int(
            metrics.get(
                "latency_ms",
                0,
            )
        ),

        "unsupported_claims": (
            verification.get(
                "unsupported_claims",
                [],
            )
        ),

        "invalid_citations": (
            verification.get(
                "invalid_citations",
                [],
            )
        ),
    }


def build_summary(
    results: list[
        dict[str, Any]
    ],
) -> dict[str, Any]:
    total = len(results)

    completed_results = [
        item
        for item in results
        if item.get(
            "completed",
            False,
        )
    ]

    completed = len(
        completed_results
    )

    successful = sum(
        bool(
            item.get(
                "success",
                False,
            )
        )
        for item in results
    )

    citation_valid_count = sum(
        bool(
            item.get(
                "citation_valid",
                False,
            )
        )
        for item
        in completed_results
    )

    verification_pass_count = sum(
        bool(
            item.get(
                "verification_passed",
                False,
            )
        )
        for item
        in completed_results
    )

    retries = sum(
        (
            item.get(
                "iterations",
                0,
            )
            > 1
        )
        for item
        in completed_results
    )

    tool_calls = sum(
        int(
            item.get(
                "tool_calls",
                0,
            )
        )
        for item
        in completed_results
    )

    errors_count = sum(
        int(
            item.get(
                "errors_count",
                0,
            )
        )
        for item
        in completed_results
    )

    successful_tool_calls = max(
        tool_calls - errors_count,
        0,
    )

    latencies = [
        float(
            item.get(
                "latency_ms",
                0,
            )
        )
        for item
        in completed_results
        if item.get(
            "latency_ms"
        )
    ]

    coverages = [
        float(
            item.get(
                "coverage_score",
                0.0,
            )
        )
        for item
        in completed_results
    ]

    iterations = [
        float(
            item.get(
                "iterations",
                0,
            )
        )
        for item
        in completed_results
    ]

    tool_calls_per_run = [
        float(
            item.get(
                "tool_calls",
                0,
            )
        )
        for item
        in completed_results
    ]

    def percentage(
        numerator: int,
        denominator: int,
    ) -> float:
        if denominator == 0:
            return 0.0

        return round(
            numerator
            / denominator
            * 100,
            2,
        )

    return {
        "total_queries": total,

        "completed": completed,

        "completion_rate": (
            percentage(
                completed,
                total,
            )
        ),

        "research_success_rate": (
            percentage(
                successful,
                total,
            )
        ),

        "citation_validity_rate": (
            percentage(
                citation_valid_count,
                completed,
            )
        ),

        "verification_pass_rate": (
            percentage(
                verification_pass_count,
                completed,
            )
        ),

        "avg_claim_support": round(
            mean(coverages)
            * 100,
            2,
        )
        if coverages
        else 0.0,

        "tool_success_rate": (
            percentage(
                successful_tool_calls,
                tool_calls,
            )
            if tool_calls
            else 0.0
        ),

        "retry_rate": (
            percentage(
                retries,
                completed,
            )
        ),

        "avg_iterations": round(
            mean(iterations),
            2,
        )
        if iterations
        else 0.0,

        "avg_tool_calls": round(
            mean(
                tool_calls_per_run
            ),
            2,
        )
        if tool_calls_per_run
        else 0.0,

        "p50_latency_ms": round(
            percentile(
                latencies,
                50,
            ),
            2,
        ),

        "p95_latency_ms": round(
            percentile(
                latencies,
                95,
            ),
            2,
        ),
    }


def print_summary(
    summary: dict[str, Any],
) -> None:
    print()
    print("=" * 52)
    print(
        "AI RESEARCH AGENT EVALUATION"
    )
    print("=" * 52)

    print(
        f"Queries               "
        f"{summary['total_queries']}"
    )

    print(
        f"Completed             "
        f"{summary['completed']}"
    )

    print(
        f"Completion rate       "
        f"{summary['completion_rate']:.2f}%"
    )

    print(
        f"Research success      "
        f"{summary['research_success_rate']:.2f}%"
    )

    print(
        f"Citation validity     "
        f"{summary['citation_validity_rate']:.2f}%"
    )

    print(
        f"Verification pass     "
        f"{summary['verification_pass_rate']:.2f}%"
    )

    print(
        f"Claim support         "
        f"{summary['avg_claim_support']:.2f}%"
    )

    print(
        f"Tool success          "
        f"{summary['tool_success_rate']:.2f}%"
    )

    print(
        f"Retry rate            "
        f"{summary['retry_rate']:.2f}%"
    )

    print(
        f"Avg iterations        "
        f"{summary['avg_iterations']:.2f}"
    )

    print(
        f"Avg tool calls        "
        f"{summary['avg_tool_calls']:.2f}"
    )

    print(
        f"p50 latency           "
        f"{summary['p50_latency_ms'] / 1000:.2f}s"
    )

    print(
        f"p95 latency           "
        f"{summary['p95_latency_ms'] / 1000:.2f}s"
    )

    print("=" * 52)


def save_report(
    results: list[
        dict[str, Any]
    ],
    summary: dict[str, Any],
) -> Path:
    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = (
        datetime.now(UTC)
        .strftime(
            "%Y%m%dT%H%M%SZ"
        )
    )

    report = {
        "generated_at": (
            datetime.now(UTC)
            .isoformat()
        ),
        "summary": summary,
        "results": results,
    }

    path = (
        REPORT_DIR
        / f"evaluation-{timestamp}.json"
    )

    path.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    latest_path = (
        REPORT_DIR
        / "latest.json"
    )

    latest_path.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return path


async def run(
    *,
    dataset_path: Path,
    base_url: str,
    concurrency: int,
    limit: int | None,
) -> None:
    cases = json.loads(
        dataset_path.read_text(
            encoding="utf-8"
        )
    )

    if limit is not None:
        cases = cases[:limit]

    semaphore = asyncio.Semaphore(
        concurrency
    )

    timeout = httpx.Timeout(
        180.0
    )

    async with httpx.AsyncClient(
        base_url=base_url,
        timeout=timeout,
    ) as client:
        tasks = [
            evaluate_case(
                client,
                semaphore,
                case,
            )
            for case in cases
        ]

        results = await asyncio.gather(
            *tasks
        )

    summary = build_summary(
        results
    )

    print_summary(
        summary
    )

    report_path = save_report(
        results,
        summary,
    )

    print()
    print(
        f"Report saved to: "
        f"{report_path}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET,
    )

    parser.add_argument(
        "--base-url",
        default=(
            "http://localhost:8001"
        ),
    )

    parser.add_argument(
        "--concurrency",
        type=int,
        default=2,
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
    )

    args = parser.parse_args()

    asyncio.run(
        run(
            dataset_path=args.dataset,
            base_url=args.base_url,
            concurrency=args.concurrency,
            limit=args.limit,
        )
    )


if __name__ == "__main__":
    main()
