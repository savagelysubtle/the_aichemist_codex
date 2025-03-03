"""Asynchronous SQLite operations for The Aichemist Codex."""

import logging
from pathlib import Path
from typing import Any, List, Tuple

import aiosqlite

logger = logging.getLogger(__name__)


class AsyncSQL:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    async def execute(
        self, query: str, params: Tuple = (), commit: bool = False
    ) -> None:
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(query, params)
                if commit:
                    await db.commit()
        except Exception as e:
            logger.error(f"Error executing query: {query} with params {params}: {e}")

    async def fetchall(self, query: str, params: Tuple = ()) -> List[Tuple[Any, ...]]:
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(query, params) as cursor:
                    rows = await cursor.fetchall()
                    return rows
        except Exception as e:
            logger.error(
                f"Error fetching rows for query: {query} with params {params}: {e}"
            )
            return []

    async def fetchone(self, query: str, params: Tuple = ()) -> Tuple[Any, ...]:
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(query, params) as cursor:
                    row = await cursor.fetchone()
                    return row
        except Exception as e:
            logger.error(
                f"Error fetching one for query: {query} with params {params}: {e}"
            )
            return None

    async def executemany(self, query: str, params_list: List[Tuple]) -> None:
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.executemany(query, params_list)
                await db.commit()
        except Exception as e:
            logger.error(
                f"Error executing many for query: {query} with params {params_list}: {e}"
            )
