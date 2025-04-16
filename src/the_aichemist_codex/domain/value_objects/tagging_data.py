from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class FileDataForTagging:
    """Value object containing file data needed for tag suggestion."""

    path: Path
    mime_type: str
    keywords: list[str] = field(default_factory=list)
    topics: list[dict[str, Any]] = field(default_factory=list)
    content_sample: str | None = None

    def __post_init__(self: "FileDataForTagging") -> None:
        """Ensure path is a Path object."""
        if isinstance(self.path, str):
            self.path = Path(self.path)
