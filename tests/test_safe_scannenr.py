from common.safety import SafeDirectoryScanner


def test_symlink_safety(tmp_path):
    base_dir = tmp_path / "project"
    base_dir.mkdir()

    safe_target = base_dir / "safe_file.txt"
    safe_target.touch()

    unsafe_target = tmp_path / "outside_file.txt"
    unsafe_target.touch()

    symlink_safe = base_dir / "safe_link"
    symlink_safe.symlink_to(safe_target)

    symlink_unsafe = base_dir / "unsafe_link"
    symlink_unsafe.symlink_to(unsafe_target)

    scanner = SafeDirectoryScanner()
    assert scanner.is_safe_path(symlink_safe, base_dir)
    assert not scanner.is_safe_path(symlink_unsafe, base_dir)
