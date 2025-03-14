from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


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
    error: Optional[str] = None
    parsed_data: Optional[Any] = None

    # Content-based metadata fields
    tags: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    topics: List[Dict[str, float]] = field(default_factory=list)
    entities: Dict[str, List[str]] = field(default_factory=dict)
    language: Optional[str] = None
    content_type: Optional[str] = None
    category: Optional[str] = None
    summary: Optional[str] = None

    # For code files
    programming_language: Optional[str] = None
    imports: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    complexity_score: Optional[float] = None

    # For document files
    title: Optional[str] = None
    author: Optional[str] = None
    creation_date: Optional[str] = None
    modified_date: Optional[str] = None

    # Extraction metadata
    extraction_complete: bool = False
    extraction_confidence: float = 0.0
    extraction_time: float = 0.0
