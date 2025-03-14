# test_sqlasync_io.py
import pytest

from backend.utils.sqlasync_io import AsyncSQL


@pytest.mark.asyncio
async def test_async_sql_execute(tmp_path):
    # Create a temporary SQLite database.
    db_path = tmp_path / "test.db"
    sql = AsyncSQL(db_path)
    await sql.execute(
        "CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT)", commit=True
    )
    await sql.execute("INSERT INTO test (value) VALUES (?)", ("example",), commit=True)
    rows = await sql.fetchall("SELECT value FROM test")
    assert rows[0][0] == "example"
