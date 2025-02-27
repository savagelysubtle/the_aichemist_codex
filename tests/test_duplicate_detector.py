from pathlib import Path

from aichemist_codex.file_manager.duplicate_detector import DuplicateDetector


def test_duplicate_detection(tmp_path: Path):
    # Create two files with identical content and one with unique content.
    file1 = tmp_path / "file1.txt"
    file1.write_text("duplicate content")

    file2 = tmp_path / "file2.txt"
    file2.write_text("duplicate content")

    file3 = tmp_path / "file3.txt"
    file3.write_text("unique content")

    detector = DuplicateDetector()
    detector.scan_directory(tmp_path)
    duplicates = detector.get_duplicates()

    # Check that at least one hash has two files (file1 and file2).
    dup_found = False
    for files in duplicates.values():
        names = [f.name for f in files]
        if "file1.txt" in names and "file2.txt" in names:
            dup_found = True
            assert len(files) == 2
    assert dup_found, "Duplicate files not detected"
