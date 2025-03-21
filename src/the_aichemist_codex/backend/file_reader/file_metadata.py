from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class FileMetadata:
    """Class for storing file metadata.

    This class holds basic file information as well as rich metadata
    extracted from file content through content analysis.
    """

    path: Path
    mime_type: str
    size: int
    extension: str
    preview: str
    error: str | None = None
    parsed_data: Any | None = None

    # Content-based metadata fields
    tags: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    topics: list[dict[str, float]] = field(default_factory=list)
    entities: dict[str, list[str]] = field(default_factory=dict)
    language: str | None = None
    content_type: str | None = None
    category: str | None = None
    summary: str | None = None

    # For code files
    programming_language: str | None = None
    imports: list[str] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)
    classes: list[str] = field(default_factory=list)
    complexity_score: float | None = None

    # For document files
    title: str | None = None
    author: str | None = None
    creation_date: str | None = None
    modified_date: str | None = None

    # Extraction metadata
    extraction_complete: bool = False
    extraction_confidence: float = 0.0
    extraction_time: float = 0.0
