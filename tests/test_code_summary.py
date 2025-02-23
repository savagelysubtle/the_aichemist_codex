import os

import pytest

from project_reader.code_summary import process_file, summarize_code


@pytest.mark.asyncio
async def test_process_python_file(tmp_path):
    """Test AST parsing for function and class extraction."""
    test_file = tmp_path / "sample.py"
    test_file.write_text(
        """
def hello(name):
    return f"Hello, {name}!"

class Greeter:
    def __init__(self, name):
        self.name = name
    """
    )

    file_path, summary, gpt_summary = await process_file(test_file)

    assert os.path.normpath(file_path) == os.path.normpath(str(test_file.resolve()))
    assert any(entry["name"] == "hello" for entry in summary)
    assert any(entry["name"] == "Greeter" for entry in summary)
    assert "Function `hello`" in gpt_summary


@pytest.mark.asyncio
async def test_summarize_code(tmp_path):
    """Test summarizing an entire directory of Python files."""
    code_dir = tmp_path / "code"
    code_dir.mkdir()
    (code_dir / "file1.py").write_text("def foo(): pass")
    (code_dir / "file2.py").write_text("class Bar: pass")

    summaries, gpt_summaries = await summarize_code(code_dir)

    assert any("file1.py" in key for key in summaries)
    assert any("file2.py" in key for key in summaries)
    assert any("Function `foo`" in value for value in gpt_summaries.values())
    assert any("Class `Bar`" in value for value in gpt_summaries.values())
