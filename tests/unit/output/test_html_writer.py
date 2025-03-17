from pathlib import Path

import pytest

from backend.src.output_formatter.html_writer import save_as_html


@pytest.mark.asyncio
@pytest.mark.unit
async def test_html_writer(tmp_path: Path) -> None:
    data = {"file.py": ["function1", "function2"]}
    output_file = tmp_path / "output.html"
    await save_as_html(output_file, data)
    content = output_file.read_text(encoding="utf-8")
    assert "<h1>Project Code Summary</h1>" in content  # noqa: S101
