"""Asynchronous SQLite operations for The Aichemist Codex."""

import logging
from pathlib import Path
from typing import Any

import aiosqlite

logger = logging.getLogger(__name__)


class AsyncSQL:
    """Provides asynchronous SQL operations."""

    def __init__(self, db_path: Path) -> None:
        """Initialize with database path."""
        self.db_path = db_path

    async def execute(
        self, query: str, params: tuple[Any, ...] = (), commit: bool = False
    ) -> None:
        """Execute a SQL query asynchronously."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(query, params)
                if commit:
                    await db.commit()
        except Exception as e:
            logger.error(f"Error executing query: {query} with params {params}: {e}")

    async def fetchall(
        self, query: str, params: tuple[Any, ...] = ()
    ) -> list[tuple[Any, ...]]:
        """Fetch all rows from a query asynchronously."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(query, params) as cursor:
                    rows = await cursor.fetchall()
                    # Convert aiosqlite.Row objects to tuples
                    return [tuple(row) for row in rows]
        except Exception as e:
            logger.error(
                f"Error fetching rows for query: {query} with params {params}: {e}"
            )
            return []

    async def fetchone(
        self, query: str, params: tuple[Any, ...] = ()
    ) -> tuple[Any, ...] | None:
        """Fetch one row from a query asynchronously."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(query, params) as cursor:
                    row = await cursor.fetchone()
                    # Convert aiosqlite.Row object to tuple if not None
                    return tuple(row) if row is not None else None
        except Exception as e:
            logger.error(
                f"Error fetching row for query: {query} with params {params}: {e}"
            )
            return None

    async def executemany(self, query: str, params_list: list[tuple]) -> None:
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.executemany(query, params_list)
                await db.commit()
        except Exception as e:
            logger.error(
                f"Error executing many for query: {query} with params "
                f"{params_list}: {e}"
            )
