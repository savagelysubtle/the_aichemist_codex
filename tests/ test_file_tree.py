import pytest

from project_reader.file_tree import FileTreeGenerator


@pytest.mark.asyncio
async def test_generate_file_tree(tmp_path):
    """Test generating a file tree with various file types and structures."""
    root_dir = tmp_path / "test_project"
    root_dir.mkdir()

    (root_dir / "main.py").touch()
    (root_dir / "subdir").mkdir()
    (root_dir / "subdir" / "module.py").touch()

    generator = FileTreeGenerator()
    result = await generator.generate(root_dir)

    assert "main.py" in result
    assert "subdir" in result
    assert "module.py" in result["subdir"]
