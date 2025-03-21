"""File reading and parsing module for The Aichemist Codex."""

from .file_metadata import FileMetadata
from .file_reader import FileReader
from .ocr_parser import OCRParser
from .parsers import (
    ArchiveParser,
    BaseParser,
    CodeParser,
    CsvParser,
    DocumentParser,
    JsonParser,
    SpreadsheetParser,
    TextParser,
    VectorParser,
    XmlParser,
    YamlParser,
    get_parser_for_mime_type,
)

__all__ = [
    "ArchiveParser",
    "BaseParser",
    "CodeParser",
    "CsvParser",
    "DocumentParser",
    "FileMetadata",
    "FileReader",
    "JsonParser",
    "OCRParser",
    "SpreadsheetParser",
    "TextParser",
    "VectorParser",
    "XmlParser",
    "YamlParser",
    "get_parser_for_mime_type",
]
