"""Asynchronous SQL operations for The AIchemist Codex."""

import asyncio
import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)


class AsyncSQL:
    """Provides asynchronous SQLite database operations."""

    def __init__(self, db_path: Path):
        """
        Initialize AsyncSQL with database path.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._connection_lock = asyncio.Lock()

    async def execute(
        self, sql: str, params: tuple | dict | None = None, commit: bool = False
    ) -> None:
        """
        Execute an SQL statement asynchronously.

        Args:
            sql: SQL statement to execute
            params: Parameters for the SQL statement
            commit: Whether to commit the transaction
        """
        async with self._connection_lock:
            try:

                def _execute():
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()

                    if params is None:
                        cursor.execute(sql)
                    else:
                        cursor.execute(sql, params)

                    if commit:
                        conn.commit()

                    cursor.close()
                    conn.close()

                await asyncio.to_thread(_execute)
            except Exception as e:
                logger.error(f"Error executing SQL: {e}")
                raise

    async def executemany(self, sql: str, params_list: list[tuple]) -> None:
        """
        Execute an SQL statement with multiple parameter sets.

        Args:
            sql: SQL statement to execute
            params_list: List of parameter tuples
        """
        async with self._connection_lock:
            try:

                def _executemany():
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    cursor.executemany(sql, params_list)
                    conn.commit()
                    cursor.close()
                    conn.close()

                await asyncio.to_thread(_executemany)
            except Exception as e:
                logger.error(f"Error executing batch SQL: {e}")
                raise

    async def fetchone(
        self, sql: str, params: tuple | dict | None = None
    ) -> tuple | None:
        """
        Fetch a single row from the database.

        Args:
            sql: SQL query to execute
            params: Parameters for the SQL query

        Returns:
            A single result row or None
        """
        async with self._connection_lock:
            try:

                def _fetchone():
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()

                    if params is None:
                        cursor.execute(sql)
                    else:
                        cursor.execute(sql, params)

                    row = cursor.fetchone()
                    cursor.close()
                    conn.close()
                    return row

                return await asyncio.to_thread(_fetchone)
            except Exception as e:
                logger.error(f"Error fetching row: {e}")
                return None

    async def fetchall(
        self, sql: str, params: tuple | dict | None = None
    ) -> list[tuple]:
        """
        Fetch all rows from the database.

        Args:
            sql: SQL query to execute
            params: Parameters for the SQL query

        Returns:
            List of result rows
        """
        async with self._connection_lock:
            try:

                def _fetchall():
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()

                    if params is None:
                        cursor.execute(sql)
                    else:
                        cursor.execute(sql, params)

                    rows = cursor.fetchall()
                    cursor.close()
                    conn.close()
                    return rows

                return await asyncio.to_thread(_fetchall)
            except Exception as e:
                logger.error(f"Error fetching rows: {e}")
                return []

    async def execute_script(self, script: str) -> None:
        """
        Execute an SQL script asynchronously.

        Args:
            script: SQL script to execute
        """
        async with self._connection_lock:
            try:

                def _execute_script():
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    cursor.executescript(script)
                    conn.commit()
                    cursor.close()
                    conn.close()

                await asyncio.to_thread(_execute_script)
            except Exception as e:
                logger.error(f"Error executing SQL script: {e}")
                raise

    async def create_tables(self, table_definitions: dict[str, str]) -> None:
        """
        Create multiple tables from definitions.

        Args:
            table_definitions: Dictionary mapping table names to CREATE TABLE statements
        """
        for table_name, create_statement in table_definitions.items():
            try:
                await self.execute(create_statement, commit=True)
                logger.info(f"Created table: {table_name}")
            except Exception as e:
                logger.error(f"Error creating table {table_name}: {e}")
                raise
