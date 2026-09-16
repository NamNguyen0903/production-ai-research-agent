from psycopg_pool import (
    AsyncConnectionPool,
)


def create_postgres_pool(
    postgres_uri: str,
) -> AsyncConnectionPool:
    return AsyncConnectionPool(
        conninfo=postgres_uri,
        min_size=1,
        max_size=5,
        open=False,
    )
