# test_csv_writer.py
import csv
from pathlib import Path

import pytest

from backend.src.output_formatter.csv_writer import save_as_csv


@pytest.mark.asyncio
async def test_csv_writer(tmp_path: Path) -> None:
    # Format data as required by save_as_csv: {file_path: [items]}
    data = {
        "test_file.py": [
            {"type": "function", "name": "Alice", "args": [], "lineno": 30},
            {"type": "function", "name": "Bob", "args": [], "lineno": 25},
        ]
    }
    output_file = tmp_path / "output.csv"
    await save_as_csv(output_file, data)

    with open(output_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert rows[0]["Name"] == "Alice"  # noqa: S101
    assert rows[0]["Type"] == "function"  # noqa: S101
    assert rows[1]["Line Number"] == "25"  # noqa: S101
