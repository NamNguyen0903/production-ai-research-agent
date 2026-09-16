from typing import Any

from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

CREATE_RESEARCH_RUNS_TABLE = """
CREATE TABLE IF NOT EXISTS research_runs (
    run_id UUID PRIMARY KEY,
    query TEXT NOT NULL,

    status VARCHAR(32) NOT NULL,

    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,

    latency_ms INTEGER,

    tool_calls INTEGER NOT NULL DEFAULT 0,
    iterations INTEGER NOT NULL DEFAULT 0,
    sources_found INTEGER NOT NULL DEFAULT 0,

    verification_score DOUBLE PRECISION,

    error TEXT
);
"""


class ResearchRunRepository:
    def __init__(
        self,
        pool: AsyncConnectionPool,
    ) -> None:
        self._pool = pool

    async def setup(self) -> None:
        async with self._pool.connection() as conn:
            await conn.execute(CREATE_RESEARCH_RUNS_TABLE)

            await conn.commit()

    async def ping(self) -> bool:
        async with self._pool.connection() as conn:
            cursor = await conn.execute("SELECT 1")

            row = await cursor.fetchone()

            return row is not None

    async def create_run(
        self,
        run_id: str,
        query: str,
    ) -> None:
        async with self._pool.connection() as conn:
            await conn.execute(
                """
                INSERT INTO research_runs (
                    run_id,
                    query,
                    status
                )
                VALUES (%s, %s, 'running')
                """,
                (
                    run_id,
                    query,
                ),
            )

            await conn.commit()

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
        async with self._pool.connection() as conn:
            await conn.execute(
                """
                UPDATE research_runs
                SET
                    status = 'completed',
                    completed_at = NOW(),
                    latency_ms = %s,
                    tool_calls = %s,
                    iterations = %s,
                    sources_found = %s,
                    verification_score = %s
                WHERE run_id = %s
                """,
                (
                    latency_ms,
                    tool_calls,
                    iterations,
                    sources_found,
                    verification_score,
                    run_id,
                ),
            )

            await conn.commit()

    async def fail_run(
        self,
        run_id: str,
        error: str,
    ) -> None:
        async with self._pool.connection() as conn:
            await conn.execute(
                """
                UPDATE research_runs
                SET
                    status = 'failed',
                    completed_at = NOW(),
                    error = %s
                WHERE run_id = %s
                """,
                (
                    error,
                    run_id,
                ),
            )

            await conn.commit()

    async def get_run(
        self,
        run_id: str,
    ) -> dict[str, Any] | None:
        async with (
            self._pool.connection() as conn,
            conn.cursor(row_factory=dict_row) as cursor,
        ):
            await cursor.execute(
                """
                    SELECT
                        run_id,
                        query,
                        status,
                        started_at,
                        completed_at,
                        latency_ms,
                        tool_calls,
                        iterations,
                        sources_found,
                        verification_score,
                        error
                    FROM research_runs
                    WHERE run_id = %s
                    """,
                (run_id,),
            )

            row = await cursor.fetchone()

            if row is None:
                return None

            return dict(row)
