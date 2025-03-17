import pytest

from backend.src.project_reader.token_counter import TokenAnalyzer


@pytest.mark.unit
def test_token_estimation() -> None:
    """Test the token count estimation of a given text."""
    analyzer = TokenAnalyzer()

    text = "Hello world! This is a test sentence."
    token_count = analyzer.estimate(text)

    assert isinstance(token_count, int)  # noqa: S101
    assert token_count > 0  # noqa: S101
