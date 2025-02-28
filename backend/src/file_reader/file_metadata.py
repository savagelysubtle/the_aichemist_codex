from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


@dataclass
class FileMetadata:
    """Class for storing file metadata."""

    path: Path
    mime_type: str
    size: int
    extension: str
    preview: str
    error: Optional[str] = None
    parsed_data: Optional[Any] = None
