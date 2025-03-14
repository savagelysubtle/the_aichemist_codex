from src.project_reader.token_counter import TokenAnalyzer


def test_token_estimation():
    """Test the token count estimation of a given text."""
    analyzer = TokenAnalyzer()

    text = "Hello world! This is a test sentence."
    token_count = analyzer.estimate(text)

    assert isinstance(token_count, int)
    assert token_count > 0
