import pytest

# test_tags.py
from backend.src.project_reader.tags import parse_tag


@pytest.mark.tagging
@pytest.mark.unit
def test_parse_tag() -> None:
    tag_str = "  exampleTag  "
    tag = parse_tag(tag_str)
    assert tag.name == "exampleTag"  # noqa: S101
