# test_sqlasync_io.py
from pathlib import Path

import pytest

from backend.src.utils.sqlasync_io import AsyncSQL


@pytest.mark.asyncio
@pytest.mark.unit
async def test_async_sql_execute(tmp_path: Path) -> None:
    # Create a temporary SQLite database.
    db_path = tmp_path / "test.db"
    sql = AsyncSQL(db_path)
    await sql.execute(
        "CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT)", commit=True
    )
    await sql.execute("INSERT INTO test (value) VALUES (?)", ("example",), commit=True)
    rows = await sql.fetchall("SELECT value FROM test")
    assert rows[0][0] == "example"  # noqa: S101
