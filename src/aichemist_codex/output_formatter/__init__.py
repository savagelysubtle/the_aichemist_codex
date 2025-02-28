"""Output handling module for different file formats."""

from .json_writer import save_as_json
from .markdown_writer import save_as_markdown

__all__ = ["save_as_markdown", "save_as_json"]
