import datetime
from pathlib import Path

from backend.src.file_manager.file_mover import FileMover


def test_auto_folder_structure(tmp_path: Path):
    # Create a temporary file.
    file_path = tmp_path / "testfile.txt"
    file_path.write_text("test")

    # Determine expected folder from the file's creation time.
    st_ctime = file_path.stat().st_ctime
    dt = datetime.datetime.fromtimestamp(st_ctime)
    expected_date_folder = dt.strftime("%Y-%m")

    base_dir = tmp_path / "base"
    base_dir.mkdir()

    mover = FileMover(base_dir)
    target_dir = mover.auto_folder_structure(file_path)

    # Expected target: base/organized/txt/YYYY-MM
    expected_dir = base_dir / "organized" / "txt" / expected_date_folder
    assert target_dir == expected_dir
