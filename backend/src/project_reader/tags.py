# src/project_reader/tags.py

class Tag:
    def __init__(self, name: str):
        self.name = name

    def __repr__(self):
        return f"Tag({self.name})"

def parse_tag(tag_str: str):
    """Parses a tag string into a Tag object"""
    return Tag(tag_str.strip())
