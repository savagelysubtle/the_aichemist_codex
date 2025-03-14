from pathlib import Path

import pytest

from backend.project_reader.code_summary import process_file


@pytest.mark.asyncio
async def test_function_metadata_extraction(tmp_path):
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

    # Normalize paths to ensure Windows/Linux compatibility
    assert Path(file_path).as_posix() == test_file.resolve().as_posix()
    assert summaries[0]["name"] == "my_func"
    assert summaries[0]["decorators"] == ["staticmethod"]
    assert summaries[0]["return_type"] == "bool"


@pytest.mark.asyncio
async def test_class_extraction(tmp_path):
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

    # Normalize paths before assertion
    assert Path(file_path).as_posix() == test_file.resolve().as_posix()
    assert any(item["name"] == "MyClass" for item in summaries)

    class_summary = next(item for item in summaries if item["name"] == "MyClass")
    assert "method_one" in class_summary["methods"]
    assert "method_two" in class_summary["methods"]
