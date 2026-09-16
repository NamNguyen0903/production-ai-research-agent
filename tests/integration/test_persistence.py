import os
from typing import TypedDict
from uuid import uuid4

import pytest
from langgraph.checkpoint.postgres.aio import (
    AsyncPostgresSaver,
)
from langgraph.graph import (
    END,
    START,
    StateGraph,
)

from app.core.config import get_settings
from app.db.factory import (
    create_postgres_pool,
)
from app.db.postgres import (
    ResearchRunRepository,
)

RUN_INFRA_TESTS = os.getenv("RUN_INFRA_TESTS") == "1"


pytestmark = pytest.mark.skipif(
    not RUN_INFRA_TESTS,
    reason=("Infrastructure tests disabled. Run with RUN_INFRA_TESTS=1."),
)


@pytest.mark.asyncio
async def test_research_run_repository_persists_run():
    settings = get_settings()

    pool = create_postgres_pool(settings.postgres_uri)

    await pool.open()

    try:
        repository = ResearchRunRepository(pool)

        await repository.setup()

        run_id = str(uuid4())

        await repository.create_run(
            run_id=run_id,
            query=("Research small language models"),
        )

        running = await repository.get_run(run_id)

        assert running is not None

        assert str(running["run_id"]) == run_id

        assert running["status"] == "running"

        assert running["query"] == ("Research small language models")

        await repository.complete_run(
            run_id,
            latency_ms=1500,
            tool_calls=3,
            iterations=1,
            sources_found=10,
            verification_score=0.9,
        )

        completed = await repository.get_run(run_id)

        assert completed is not None

        assert completed["status"] == "completed"

        assert completed["latency_ms"] == 1500

        assert completed["tool_calls"] == 3

        assert completed["iterations"] == 1

        assert completed["sources_found"] == 10

        assert completed["verification_score"] == pytest.approx(0.9)

        assert completed["completed_at"] is not None

    finally:
        await pool.close()


class CheckpointState(
    TypedDict,
):
    value: int


async def increment_node(
    state: CheckpointState,
) -> dict[str, int]:
    return {"value": (state["value"] + 1)}


@pytest.mark.asyncio
async def test_langgraph_checkpoint_persists_state():
    settings = get_settings()

    thread_id = str(uuid4())

    async with AsyncPostgresSaver.from_conn_string(
        settings.postgres_uri
    ) as checkpointer:
        await checkpointer.setup()

        builder = StateGraph(CheckpointState)

        builder.add_node(
            "increment",
            increment_node,
        )

        builder.add_edge(
            START,
            "increment",
        )

        builder.add_edge(
            "increment",
            END,
        )

        graph = builder.compile(checkpointer=checkpointer)

        config = {
            "configurable": {
                "thread_id": thread_id,
            }
        }

        result = await graph.ainvoke(
            {"value": 0},
            config=config,
        )

        assert result["value"] == 1

        snapshot = await graph.aget_state(config)

        assert snapshot.values["value"] == 1

        assert snapshot.config["configurable"]["thread_id"] == thread_id
