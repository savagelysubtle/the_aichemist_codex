# test_version.py
from backend.project_reader.version import InvalidVersion, Version


def test_valid_version():
    v = Version("1.0.0")
    assert "1.0.0" in repr(v)


def test_invalid_version():
    try:
        Version("")
        assert False, "InvalidVersion should have been raised."
    except InvalidVersion:
        assert True
