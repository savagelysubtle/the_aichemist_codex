from pathlib import Path
from typing import Any

import pytest

from backend.src.project_reader.code_summary import process_file


@pytest.mark.asyncio
async def test_function_metadata_extraction(tmp_path: Path) -> None:
    """Test extracting function metadata, including decorators and return types."""
    test_file = tmp_path / "test_script.py"
    test_file.write_text(
        """
@staticmethod
def my_func(a: int, b: str) -> bool:
    return True
"""
    )

    file_path, summaries = await process_file(test_file)
    # Annotate summaries as list of dictionaries
    summaries_list: list[dict[str, Any]] = summaries  # type: ignore

    # Normalize paths to ensure Windows/Linux compatibility
    assert Path(file_path).as_posix() == test_file.resolve().as_posix()  # noqa: S101
    assert summaries_list[0]["name"] == "my_func"  # noqa: S101
    assert summaries_list[0]["decorators"] == ["staticmethod"]  # noqa: S101
    assert summaries_list[0]["return_type"] == "bool"  # noqa: S101


@pytest.mark.asyncio
async def test_class_extraction(tmp_path: Path) -> None:
    """Test extracting class metadata, including methods."""
    test_file = tmp_path / "test_class.py"
    test_file.write_text(
        """
class MyClass:
    def method_one(self):
        pass

    def method_two(self, x: int) -> str:
        return str(x)
"""
    )

    file_path, summaries = await process_file(test_file)
    # Annotate summaries as list of dictionaries
    summaries_list: list[dict[str, Any]] = summaries  # type: ignore

    # Normalize paths before assertion
    assert Path(file_path).as_posix() == test_file.resolve().as_posix()  # noqa: S101
    assert any(item["name"] == "MyClass" for item in summaries_list)  # noqa: S101

    class_summary = next(item for item in summaries_list if item["name"] == "MyClass")
    assert "method_one" in class_summary["methods"]  # noqa: S101
    assert "method_two" in class_summary["methods"]  # noqa: S101
