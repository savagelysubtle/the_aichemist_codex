import pytest


@pytest.mark.unit
def test_simple_addition():
    """Test simple addition."""
    assert 1 + 1 == 2  # noqa: S101


@pytest.mark.unit
def test_simple_string():
    """Test simple string operations."""
    assert "hello" + " world" == "hello world"  # noqa: S101


@pytest.mark.unit
@pytest.mark.parametrize(
    "input_value,expected",
    [
        (1, 1),
        (2, 4),
        (3, 9),
        (4, 16),
    ],
)
def test_square_function(input_value, expected):
    """Test a simple square function."""

    def square(x):
        return x * x

    assert square(input_value) == expected  # noqa: S101
