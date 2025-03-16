# test_patterns.py
from backend.src.utils.patterns import pattern_matcher


def test_pattern_matcher_should_ignore() -> None:
    # Assuming pattern_matcher.ignore_patterns includes some known patterns.
    # For testing, we update ignore_patterns.
    pattern_matcher.ignore_patterns.update({"*.log", "temp"})
    assert pattern_matcher.should_ignore("error.log")  # noqa: S101
    assert pattern_matcher.should_ignore("temp/file.txt")  # noqa: S101
    assert not pattern_matcher.should_ignore("file.txt")  # noqa: S101
