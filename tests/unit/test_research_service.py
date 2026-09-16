from typing import Any

import pytest

from app.models.verification import (
    VerificationResult,
)
from app.services.research_service import (
    ResearchService,
)


class FakeGraph:
    def __init__(
        self,
        result: dict[str, Any] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.result = result
        self.error = error

        self.received_state: dict[str, Any] | None = None

        self.received_config: dict[str, Any] | None = None

    async def ainvoke(
        self,
        state: dict[str, Any],
        config: dict[str, Any],
    ) -> dict[str, Any]:
        self.received_state = state
        self.received_config = config

        if self.error is not None:
            raise self.error

        assert self.result is not None

        return self.result


class FakeRepository:
    def __init__(self) -> None:
        self.created_runs: list[dict[str, Any]] = []

        self.completed_runs: list[dict[str, Any]] = []

        self.failed_runs: list[dict[str, Any]] = []

    async def create_run(
        self,
        run_id: str,
        query: str,
    ) -> None:
        self.created_runs.append(
            {
                "run_id": run_id,
                "query": query,
            }
        )

    async def complete_run(
        self,
        run_id: str,
        *,
        latency_ms: int,
        tool_calls: int,
        iterations: int,
        sources_found: int,
        verification_score: float | None,
    ) -> None:
        self.completed_runs.append(
            {
                "run_id": run_id,
                "latency_ms": latency_ms,
                "tool_calls": tool_calls,
                "iterations": iterations,
                "sources_found": (sources_found),
                "verification_score": (verification_score),
            }
        )

    async def fail_run(
        self,
        run_id: str,
        error: str,
    ) -> None:
        self.failed_runs.append(
            {
                "run_id": run_id,
                "error": error,
            }
        )


def make_initial_state() -> dict[str, Any]:
    return {
        "run_id": "test-run-id",
        "query": ("Research small language models"),
        "plan": [],
        "evidence": [],
        "draft_answer": None,
        "used_source_ids": [],
        "verification": None,
        "retry_queries": [],
        "iteration": 0,
        "max_iterations": 2,
        "tool_calls": 0,
        "max_tool_calls": 15,
        "errors": [],
        "final_answer": None,
    }


@pytest.mark.asyncio
async def test_service_persists_successful_run():
    graph = FakeGraph(
        result={
            "query": ("Research small language models"),
            "evidence": [
                {"source_id": "src-1"},
                {"source_id": "src-2"},
            ],
            "tool_calls": 3,
            "iteration": 1,
            "verification": (
                VerificationResult(
                    passed=True,
                    coverage_score=0.9,
                    citation_valid=True,
                )
            ),
            "final_answer": "Answer",
        }
    )

    repository = FakeRepository()

    service = ResearchService(
        graph=graph,
        repository=repository,  # type: ignore[arg-type]
        recursion_limit=25,
        langfuse_enabled=False,
    )

    result = await service.run(
        run_id="test-run-id",
        initial_state=make_initial_state(),
    )

    assert len(repository.created_runs) == 1

    assert repository.created_runs[0]["run_id"] == "test-run-id"

    assert repository.created_runs[0]["query"] == "Research small language models"

    assert len(repository.completed_runs) == 1

    completed = repository.completed_runs[0]

    assert completed["run_id"] == "test-run-id"

    assert completed["tool_calls"] == 3

    assert completed["iterations"] == 1

    assert completed["sources_found"] == 2

    assert completed["verification_score"] == 0.9

    assert isinstance(
        completed["latency_ms"],
        int,
    )

    assert result["_latency_ms"] >= 0


@pytest.mark.asyncio
async def test_service_passes_thread_id_to_graph():
    graph = FakeGraph(
        result={
            "evidence": [],
            "tool_calls": 0,
            "iteration": 1,
            "verification": None,
        }
    )

    service = ResearchService(
        graph=graph,
        repository=None,
        recursion_limit=25,
        langfuse_enabled=False,
    )

    await service.run(
        run_id="thread-123",
        initial_state=make_initial_state(),
    )

    assert graph.received_config is not None

    assert graph.received_config["configurable"]["thread_id"] == "thread-123"

    assert graph.received_config["recursion_limit"] == 25


@pytest.mark.asyncio
async def test_service_passes_state_to_graph():
    graph = FakeGraph(
        result={
            "evidence": [],
            "tool_calls": 0,
            "iteration": 1,
            "verification": None,
        }
    )

    service = ResearchService(
        graph=graph,
        repository=None,
        recursion_limit=25,
        langfuse_enabled=False,
    )

    initial_state = make_initial_state()

    await service.run(
        run_id="test-run-id",
        initial_state=initial_state,
    )

    assert graph.received_state == initial_state


@pytest.mark.asyncio
async def test_service_marks_failed_run():
    graph = FakeGraph(error=RuntimeError("Graph execution failed"))

    repository = FakeRepository()

    service = ResearchService(
        graph=graph,
        repository=repository,  # type: ignore[arg-type]
        recursion_limit=25,
        langfuse_enabled=False,
    )

    with pytest.raises(
        RuntimeError,
        match="Graph execution failed",
    ):
        await service.run(
            run_id="failed-run",
            initial_state=(make_initial_state()),
        )

    assert len(repository.created_runs) == 1

    assert len(repository.failed_runs) == 1

    assert repository.failed_runs[0]["run_id"] == "failed-run"

    assert repository.failed_runs[0]["error"] == "Graph execution failed"

    assert repository.completed_runs == []


@pytest.mark.asyncio
async def test_service_works_without_repository():
    graph = FakeGraph(
        result={
            "evidence": [],
            "tool_calls": 2,
            "iteration": 1,
            "verification": None,
            "final_answer": "Answer",
        }
    )

    service = ResearchService(
        graph=graph,
        repository=None,
        recursion_limit=25,
        langfuse_enabled=False,
    )

    result = await service.run(
        run_id="no-db-run",
        initial_state=make_initial_state(),
    )

    assert result["final_answer"] == "Answer"

    assert "_latency_ms" in result
