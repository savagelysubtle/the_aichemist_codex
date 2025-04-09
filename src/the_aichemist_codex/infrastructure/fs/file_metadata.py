"""File metadata module for The AIchemist Codex."""

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
    preview: str = ""
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

    def __post_init__(self) -> None:
        """Ensure extension starts with a dot and is lowercase."""
        if self.extension and not self.extension.startswith("."):
            self.extension = f".{self.extension}"
        self.extension = self.extension.lower()

    @property
    def filename(self) -> str:
        """Get the filename from the path."""
        return self.path.name

    @classmethod
    def from_path(cls, path: Path) -> "FileMetadata":
        """Create basic metadata from a file path.

        Args:
            path: Path to the file

        Returns:
            FileMetadata object with basic information
        """
        try:
            if path.exists():
                stats = path.stat()
                size = stats.st_size
                extension = path.suffix.lower()

                # Simple mime type inference based on extension
                mime_type = cls._infer_mime_type(extension)
            else:
                size = -1
                extension = path.suffix.lower()
                mime_type = "unknown"

            return cls(
                path=path,
                mime_type=mime_type,
                size=size,
                extension=extension,
                preview="",
            )
        except Exception as e:
            return cls(
                path=path,
                mime_type="unknown",
                size=-1,
                extension=path.suffix.lower(),
                preview="",
                error=str(e),
            )

    @staticmethod
    def _infer_mime_type(extension: str) -> str:
        """Infer MIME type from file extension.

        Args:
            extension: File extension (with or without leading dot)

        Returns:
            Inferred MIME type
        """
        extension = extension.lower()
        if not extension.startswith("."):
            extension = f".{extension}"

        mime_map = {
            ".txt": "text/plain",
            ".md": "text/markdown",
            ".html": "text/html",
            ".htm": "text/html",
            ".css": "text/css",
            ".js": "application/javascript",
            ".json": "application/json",
            ".xml": "application/xml",
            ".yaml": "application/yaml",
            ".yml": "application/yaml",
            ".py": "text/x-python",
            ".java": "text/x-java",
            ".c": "text/x-c",
            ".cpp": "text/x-c++",
            ".cs": "text/x-csharp",
            ".go": "text/x-go",
            ".rs": "text/x-rust",
            ".rb": "text/x-ruby",
            ".php": "text/x-php",
            ".sh": "text/x-shellscript",
            ".bat": "text/x-bat",
            ".ps1": "text/x-powershell",
            ".pdf": "application/pdf",
            ".doc": "application/msword",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".xls": "application/vnd.ms-excel",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".ppt": "application/vnd.ms-powerpoint",
            ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".svg": "image/svg+xml",
            ".mp3": "audio/mpeg",
            ".mp4": "video/mp4",
            ".zip": "application/zip",
            ".tar": "application/x-tar",
            ".gz": "application/gzip",
            ".7z": "application/x-7z-compressed",
        }

        return mime_map.get(extension, "application/octet-stream")

    def to_dict(self) -> dict[str, Any]:
        """Convert metadata to dictionary.

        Returns:
            Dictionary representation of metadata
        """
        result = {
            "path": str(self.path),
            "filename": self.filename,
            "mime_type": self.mime_type,
            "size": self.size,
            "extension": self.extension,
            "preview_length": len(self.preview) if self.preview else 0,
            "tags": self.tags,
            "keywords": self.keywords,
            "language": self.language,
            "content_type": self.content_type,
            "category": self.category,
            "extraction_complete": self.extraction_complete,
            "extraction_confidence": self.extraction_confidence,
        }

        # Include optional fields if they have values
        if self.error:
            result["error"] = self.error
        if self.summary:
            result["summary"] = self.summary
        if self.programming_language:
            result["programming_language"] = self.programming_language
        if self.complexity_score is not None:
            result["complexity_score"] = self.complexity_score

        return result

    def __str__(self) -> str:
        """String representation of metadata."""
        return f"FileMetadata({self.path.name}, {self.mime_type}, {self.size} bytes)"
