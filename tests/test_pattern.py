from project_reader.patterns import PatternMatcher


def test_pattern_matching():
    matcher = PatternMatcher()

    # Default ignores
    assert matcher.should_ignore("__pycache__/file.py")
    assert matcher.should_ignore("node_modules/index.js")

    # Custom patterns
    matcher.add_patterns({"*.test.js", "*.log"})
    assert matcher.should_ignore("debug.log")
    assert matcher.should_ignore("test.test.js")

    # Files that should not be ignored
    assert not matcher.should_ignore("src/main.py")
    assert not matcher.should_ignore("docs/README.md")
