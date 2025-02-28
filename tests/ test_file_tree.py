import pytest

from project_reader.file_tree import FileTreeGenerator


@pytest.mark.asyncio
async def test_file_tree_generation(tmp_path):
    """Test generating a file tree with valid directories and files."""
    (tmp_path / "folder").mkdir()
    (tmp_path / "folder/file1.py").write_text("print('Hello')")
    (tmp_path / "folder/ignore.me").write_text("Ignored")

    generator = FileTreeGenerator()
    tree = await generator.generate(tmp_path)

    assert "folder" in tree
    assert "file1.py" in tree["folder"]
    assert "size" in tree["folder"]["file1.py"]
    assert "ignore.me" not in tree["folder"]  # Ensure ignore pattern works


@pytest.mark.asyncio
async def test_symlink_safety(tmp_path):
    """Ensure unsafe symlinks are not followed."""
    real_folder = tmp_path / "real_folder"
    real_folder.mkdir()
    (real_folder / "real_file.py").write_text("print('Valid')")

    symlink = tmp_path / "symlink"
    symlink.symlink_to(real_folder, target_is_directory=True)

    generator = FileTreeGenerator()
    tree = await generator.generate(tmp_path)

    assert "symlink" not in tree  # Unsafe symlink should be ignored
