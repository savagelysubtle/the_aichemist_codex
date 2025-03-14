# test_tags.py
from backend.project_reader.tags import parse_tag


def test_parse_tag():
    tag_str = "  exampleTag  "
    tag = parse_tag(tag_str)
    assert tag.name == "exampleTag"
