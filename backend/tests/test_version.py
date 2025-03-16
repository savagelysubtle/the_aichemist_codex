# test_version.py
from backend.src.project_reader.version import InvalidVersion, Version


def test_valid_version() -> None:
    v = Version("1.0.0")
    assert "1.0.0" in repr(v)  # noqa: S101


def test_invalid_version() -> None:
    try:
        Version("")
        raise AssertionError("InvalidVersion should have been raised.")
    except InvalidVersion:
        assert True  # noqa: S101
